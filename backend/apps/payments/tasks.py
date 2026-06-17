"""
SmartPark AI — Celery Tasks
============================
Periodic and async tasks for:
  - YOLOv8 occupancy detection
  - Demand forecasting refresh
  - Fraud detection sweep
  - Refund processing
  - FCM push notifications
"""

from celery import shared_task
from celery.utils.log import get_task_logger
import logging

logger = get_task_logger(__name__)


# ── Occupancy Detection ────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=3)
def run_occupancy_detection(self, lot_id: str):
    """
    Run YOLOv8 occupancy detection on a parking lot's camera feed.
    Updates ParkingSlot.is_occupied and logs to OccupancyLog.
    """
    from apps.parking.models import ParkingLot, ParkingSlot, OccupancyLog
    from ai_engine.occupancy.detector import ParkingOccupancyDetector
    from django.utils import timezone

    try:
        lot = ParkingLot.objects.get(pk=lot_id)
        if not lot.camera_feed_url:
            logger.warning(f"Lot {lot_id} has no camera feed.")
            return

        detector = ParkingOccupancyDetector()

        # Get slot regions from DB (pre-annotated bounding boxes)
        slots = ParkingSlot.objects.filter(lot=lot, is_available=True)
        slot_regions = []  # In production: load calibrated bounding boxes per slot

        detections = detector.detect_from_url(lot.camera_feed_url, slot_regions)

        for det in detections:
            if det.get("slot_id"):
                try:
                    slot = ParkingSlot.objects.get(pk=det["slot_id"])
                    slot.is_occupied = det["is_occupied"]
                    slot.occupancy_confidence = det["confidence"]
                    slot.last_detected_at = timezone.now()
                    slot.save()

                    OccupancyLog.objects.create(
                        slot=slot,
                        is_occupied=det["is_occupied"],
                        confidence=det["confidence"],
                    )
                except ParkingSlot.DoesNotExist:
                    pass

        logger.info(f"Occupancy detection complete for lot {lot_id}: {len(detections)} detections.")

    except Exception as exc:
        logger.error(f"Occupancy detection failed for lot {lot_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


@shared_task
def run_all_occupancy_detection():
    """Periodic task: run detection on all active lots with camera feeds."""
    from apps.parking.models import ParkingLot

    lots = ParkingLot.objects.filter(is_active=True).exclude(camera_feed_url="")
    for lot in lots:
        run_occupancy_detection.delay(str(lot.id))

    logger.info(f"Scheduled occupancy detection for {lots.count()} lots.")


# ── Demand Forecasting ─────────────────────────────────────────────────────────
@shared_task
def refresh_demand_forecast(lot_id: str):
    """Refresh 24-hour demand forecast for a parking lot and cache results."""
    from ai_engine.forecasting.forecaster import DemandForecaster
    from django.core.cache import cache

    forecaster = DemandForecaster()
    forecast = forecaster.predict(lot_id=lot_id, hours_ahead=24)

    cache_key = f"demand_forecast:{lot_id}"
    cache.set(cache_key, forecast, timeout=3600)  # Cache 1 hour
    logger.info(f"Demand forecast refreshed for lot {lot_id}.")
    return forecast


@shared_task
def refresh_all_forecasts():
    """Periodic: refresh forecasts for all active lots."""
    from apps.parking.models import ParkingLot

    lots = ParkingLot.objects.filter(is_active=True)
    for lot in lots:
        refresh_demand_forecast.delay(str(lot.id))


# ── Fraud Detection ────────────────────────────────────────────────────────────
@shared_task
def run_fraud_sweep():
    """Periodic fraud detection sweep across all active users."""
    from ai_engine.fraud.detector import FraudDetector

    detector = FraudDetector()
    results = detector.batch_score_users()
    suspicious = results[results["is_suspicious"] == True]
    logger.info(f"Fraud sweep: {len(suspicious)} suspicious users found.")
    return {"total": len(results), "suspicious": len(suspicious)}


@shared_task
def check_transaction_fraud(booking_id: str):
    """Check a single booking for fraud immediately after creation."""
    from ai_engine.fraud.detector import FraudDetector

    detector = FraudDetector()
    result = detector.score_transaction(booking_id)
    if result.get("is_suspicious"):
        logger.warning(f"Suspicious transaction detected: {booking_id} — {result['flags']}")
    return result


# ── Payments / Refunds ─────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=5)
def process_refund(self, booking_id: str):
    """Process Razorpay refund for early exit."""
    import razorpay
    from django.conf import settings
    from apps.bookings.models import Booking

    try:
        booking = Booking.objects.get(pk=booking_id)
        if booking.refund_amount <= 0 or not booking.razorpay_payment_id:
            return

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        refund = client.payment.refund(
            booking.razorpay_payment_id,
            {"amount": int(float(booking.refund_amount) * 100)},
        )
        booking.status = "refunded"
        booking.save()
        logger.info(f"Refund processed for booking {booking_id}: ₹{booking.refund_amount}")
        send_push_notification.delay(
            str(booking.user.id),
            "Refund Processed",
            f"₹{booking.refund_amount} refunded to your original payment method.",
        )
    except Exception as exc:
        logger.error(f"Refund failed for booking {booking_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ── FCM Push Notifications ────────────────────────────────────────────────────
@shared_task
def send_push_notification(user_id: str, title: str, body: str, data: dict = None):
    """Send Firebase Cloud Messaging push notification to a user."""
    import firebase_admin
    from firebase_admin import messaging
    from apps.users.models import User
    from django.conf import settings

    try:
        if not firebase_admin._apps:
            cred = firebase_admin.credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)

        user = User.objects.get(pk=user_id)
        if not user.fcm_token:
            return

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=user.fcm_token,
            data=data or {},
        )
        messaging.send(message)
        logger.info(f"Push notification sent to user {user_id}: {title}")
    except Exception as e:
        logger.error(f"FCM notification failed for user {user_id}: {e}")
