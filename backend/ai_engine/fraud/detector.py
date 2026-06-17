"""
SmartPark AI — Fraud Detection Engine
=======================================
Uses Isolation Forest (unsupervised anomaly detection) to flag:
  1. Abnormal booking patterns (too many short bookings)
  2. Rapid repeated slot changes
  3. Suspicious payment sequences
  4. Fake occupancy manipulation

Logs flagged events for Admin review.
"""

import numpy as np
import pandas as pd
import joblib
import logging
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from django.conf import settings

logger = logging.getLogger(__name__)


class FraudDetector:
    """
    Isolation Forest-based fraud detection.

    Anomaly features per user/transaction:
      - bookings_per_day
      - avg_booking_duration_hours
      - cancellation_rate
      - refund_rate
      - payment_failures
      - unique_lots_per_week
      - late_exit_rate
    """

    FEATURE_COLS = [
        "bookings_per_day",
        "avg_duration_hours",
        "cancellation_rate",
        "refund_rate",
        "payment_failures",
        "unique_lots_per_week",
        "late_exit_rate",
    ]

    # Contamination: expected fraction of anomalies in dataset
    CONTAMINATION = 0.05

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self._load_model()

    def _load_model(self):
        model_path = Path(settings.FRAUD_MODEL_PATH)
        scaler_path = Path(settings.ML_MODELS_DIR) / "fraud_scaler.pkl"

        if model_path.exists():
            self.model = joblib.load(model_path)
            logger.info("Fraud detection model loaded.")
        else:
            # Train a default model if none exists
            self.model = IsolationForest(
                n_estimators=200,
                contamination=self.CONTAMINATION,
                random_state=42,
                n_jobs=-1,
            )
            logger.warning("No pre-trained fraud model found. Using default Isolation Forest.")

        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)

    def _extract_user_features(self, user_id: str) -> dict:
        """Compute behavioural features for a user from DB."""
        from apps.bookings.models import Booking
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        week_ago = now - timedelta(days=7)
        day_ago = now - timedelta(days=1)

        bookings = Booking.objects.filter(user_id=user_id)
        recent_day = bookings.filter(created_at__gte=day_ago)
        recent_week = bookings.filter(created_at__gte=week_ago)

        total = bookings.count()
        cancelled = bookings.filter(status="cancelled").count()
        refunded = bookings.filter(status="refunded").count()
        payment_failures = bookings.filter(is_paid=False, status="cancelled").count()

        completed = bookings.filter(status="completed",
                                    actual_entry__isnull=False,
                                    actual_exit__isnull=False)
        durations = []
        late_exits = 0
        for b in completed:
            dur = (b.actual_exit - b.actual_entry).total_seconds() / 3600
            durations.append(dur)
            if b.actual_exit > b.scheduled_end:
                late_exits += 1

        unique_lots = recent_week.values("slot__lot_id").distinct().count()

        return {
            "bookings_per_day": recent_day.count(),
            "avg_duration_hours": float(np.mean(durations)) if durations else 0,
            "cancellation_rate": cancelled / max(total, 1),
            "refund_rate": refunded / max(total, 1),
            "payment_failures": payment_failures,
            "unique_lots_per_week": unique_lots,
            "late_exit_rate": late_exits / max(len(durations), 1),
        }

    def score_user(self, user_id: str) -> dict:
        """
        Score a user's behaviour.
        Returns: {is_suspicious, anomaly_score, features}
        """
        features = self._extract_user_features(user_id)
        X = pd.DataFrame([features])[self.FEATURE_COLS]
        X_scaled = self.scaler.transform(X) if hasattr(self.scaler, "mean_") else X.values

        # IsolationForest: -1 = anomaly, 1 = normal
        prediction = self.model.predict(X_scaled)[0]
        score = float(self.model.score_samples(X_scaled)[0])

        is_suspicious = prediction == -1
        if is_suspicious:
            logger.warning(f"FRAUD ALERT: User {user_id} flagged. Score={score:.3f}")
            self._log_fraud_event(user_id, features, score)

        return {
            "user_id": user_id,
            "is_suspicious": is_suspicious,
            "anomaly_score": round(score, 4),
            "features": features,
        }

    def score_transaction(self, booking_id: str) -> dict:
        """
        Score a specific booking transaction for anomalies.
        """
        from apps.bookings.models import Booking

        try:
            booking = Booking.objects.get(pk=booking_id)
        except Booking.DoesNotExist:
            return {"is_suspicious": False, "reason": "booking not found"}

        flags = []

        # Duration anomaly: booking < 5 minutes
        if booking.scheduled_end and booking.scheduled_start:
            dur = (booking.scheduled_end - booking.scheduled_start).total_seconds() / 60
            if dur < 5:
                flags.append("very_short_duration")

        # Same-day repeat booking at same lot
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        same_lot_today = Booking.objects.filter(
            user=booking.user,
            slot__lot=booking.slot.lot,
            created_at__date=today,
        ).count()
        if same_lot_today > 5:
            flags.append("excessive_same_lot_bookings")

        # Price anomaly: massive discount vs expected
        if booking.estimated_amount and float(booking.estimated_amount) < 1:
            flags.append("suspiciously_low_amount")

        return {
            "booking_id": str(booking.id),
            "is_suspicious": len(flags) > 0,
            "flags": flags,
        }

    def _log_fraud_event(self, user_id: str, features: dict, score: float):
        """Persist fraud event to DB for admin review."""
        try:
            from apps.analytics.models import FraudEvent
            FraudEvent.objects.create(
                user_id=user_id,
                anomaly_score=score,
                features=features,
            )
        except Exception as e:
            logger.error(f"Could not log fraud event: {e}")

    def batch_score_users(self) -> pd.DataFrame:
        """Run fraud scoring for all active users. Called by Celery periodic task."""
        from apps.users.models import User
        users = User.objects.filter(is_active=True, role="user")
        results = []
        for user in users:
            result = self.score_user(str(user.id))
            results.append(result)
        return pd.DataFrame(results)


# ── Training ───────────────────────────────────────────────────────────────────
def train_fraud_model(df: pd.DataFrame, save_dir: str = "ml_models"):
    """
    Train Isolation Forest on historical user behaviour features.
    df must contain: FEATURE_COLS (no labels needed — unsupervised)
    """
    import os
    os.makedirs(save_dir, exist_ok=True)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[FraudDetector.FEATURE_COLS].fillna(0))

    model = IsolationForest(
        n_estimators=300,
        contamination=FraudDetector.CONTAMINATION,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    joblib.dump(model,  f"{save_dir}/fraud_detector.pkl")
    joblib.dump(scaler, f"{save_dir}/fraud_scaler.pkl")
    logger.info("Fraud detection model trained and saved.")
    return model
