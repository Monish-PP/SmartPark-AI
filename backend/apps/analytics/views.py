from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Avg, Count, F
from django.utils import timezone
from datetime import timedelta, datetime, time
from django.core.cache import cache

from apps.bookings.models import Booking
from apps.parking.models import ParkingLot, ParkingSlot, OccupancyLog
from apps.users.models import User
from ai_engine.forecasting.forecaster import DemandForecaster


class OwnerDashboardView(APIView):
    """Analytics dashboard for parking lot owners."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        lots = ParkingLot.objects.filter(owner=request.user)
        now = timezone.now()
        period = request.query_params.get("period", "week")  # week, month, year

        delta = {"week": 7, "month": 30, "year": 365}.get(period, 7)
        since = now - timedelta(days=delta)

        bookings = Booking.objects.filter(slot__lot__in=lots, created_at__gte=since)

        # Revenue breakdown
        total_revenue = bookings.filter(is_paid=True).aggregate(
            total=Sum("final_amount")
        )["total"] or 0

        platform_commission = round(float(total_revenue) * 0.10, 2)
        owner_earnings = round(float(total_revenue) * 0.90, 2)

        # Occupancy stats per lot
        lot_stats = []
        for lot in lots:
            lot_bookings = bookings.filter(slot__lot=lot)
            total_slots = lot.slots.count()
            currently_occupied = lot.slots.filter(is_occupied=True).count()

            # Demand forecast
            cache_key = f"demand_forecast:{lot.id}"
            forecast = cache.get(cache_key)
            if not forecast:
                forecaster = DemandForecaster()
                forecast = forecaster.predict(str(lot.id), hours_ahead=24)
                cache.set(cache_key, forecast, timeout=3600)

            lot_stats.append({
                "lot_id": str(lot.id),
                "lot_name": lot.name,
                "total_slots": total_slots,
                "occupied_slots": currently_occupied,
                "occupancy_rate": round(currently_occupied / max(total_slots, 1), 2),
                "bookings_count": lot_bookings.count(),
                "revenue": float(lot_bookings.filter(is_paid=True).aggregate(
                    s=Sum("final_amount"))["s"] or 0),
                "avg_rating": float(lot_bookings.aggregate(
                    r=Avg("review__rating"))["r"] or 0),
                "demand_forecast_24h": forecast[:8],  # Next 4 hours (8 x 30min)
            })

        # Daily revenue trend
        daily_revenue = []
        for i in range(delta):
            day = (now - timedelta(days=delta - i - 1)).date()
            start = timezone.make_aware(datetime.combine(day, time.min), timezone.get_current_timezone())
            end = start + timedelta(days=1)
            rev = bookings.filter(
                created_at__gte=start,
                created_at__lt=end,
                is_paid=True,
            ).aggregate(s=Sum("final_amount"))["s"] or 0
            daily_revenue.append({"date": str(day), "revenue": float(rev)})

        return Response({
            "period": period,
            "total_revenue": float(total_revenue),
            "platform_commission": platform_commission,
            "owner_earnings": owner_earnings,
            "total_bookings": bookings.count(),
            "lots": lot_stats,
            "daily_revenue": daily_revenue,
        })


class AdminAnalyticsView(APIView):
    """Platform-wide analytics for administrators."""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()
        since = now - timedelta(days=30)

        bookings = Booking.objects.filter(created_at__gte=since)
        users = User.objects.filter(date_joined__gte=since)

        total_revenue = bookings.filter(is_paid=True).aggregate(
            total=Sum("final_amount"))["total"] or 0
        commission = round(float(total_revenue) * 0.10, 2)

        # Top earning lots
        top_lots = (
            Booking.objects.filter(is_paid=True, created_at__gte=since)
            .values("slot__lot__name", "slot__lot__id")
            .annotate(revenue=Sum("final_amount"), bookings=Count("id"))
            .order_by("-revenue")[:10]
        )

        # User growth
        new_users = users.filter(role="user").count()
        new_owners = users.filter(role="owner").count()

        # Fraud events
        try:
            from apps.analytics.models import FraudEvent
            fraud_events = FraudEvent.objects.filter(created_at__gte=since).count()
        except Exception:
            fraud_events = 0

        return Response({
            "total_revenue_30d": float(total_revenue),
            "platform_commission_30d": commission,
            "total_bookings_30d": bookings.count(),
            "new_users_30d": new_users,
            "new_owners_30d": new_owners,
            "fraud_events_30d": fraud_events,
            "top_earning_lots": list(top_lots),
        })


class HeatmapDataView(APIView):
    """Demand heatmap data for Google Maps overlay.

    Query params:
        type: "occupancy" | "revenue" | "demand" (default: "occupancy")
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        layer_type = request.query_params.get("type", "occupancy")
        lots = ParkingLot.objects.filter(is_active=True, is_verified=True)
        heatmap_points = []

        for lot in lots:
            total = lot.slots.count()
            occupied = lot.slots.filter(is_occupied=True).count()
            demand = occupied / max(total, 1)

            # Try enriched occupancy snapshot first, fall back to slot count
            try:
                snapshot = lot.occupancy_snapshot
                occupancy_rate = snapshot.occupancy_rate / 100.0  # convert % to 0–1
                occ_weight = round(occupancy_rate, 2)
            except Exception:
                occupancy_rate = demand
                occ_weight = round(demand, 2)

            # Revenue density: revenue per slot in last 30 days
            from datetime import timedelta
            since = timezone.now() - timedelta(days=30)
            try:
                from apps.bookings.models import Booking
                from django.db.models import Sum
                lot_revenue = Booking.objects.filter(
                    slot__lot=lot, is_paid=True, created_at__gte=since
                ).aggregate(s=Sum("final_amount"))["s"] or 0
                revenue_density = round(float(lot_revenue) / max(total, 1), 2)
            except Exception:
                revenue_density = 0

            # Demand forecast score (cached)
            from django.core.cache import cache
            cache_key = f"heatmap_forecast:{lot.id}"
            forecast_score = cache.get(cache_key)
            if forecast_score is None:
                try:
                    forecaster = DemandForecaster()
                    forecast = forecaster.predict(str(lot.id), hours_ahead=4)
                    if forecast:
                        forecast_score = round(
                            sum(f.get("predicted_occupancy_rate", 0) for f in forecast)
                            / len(forecast), 2
                        )
                    else:
                        forecast_score = 0.0
                except Exception:
                    forecast_score = 0.0
                cache.set(cache_key, forecast_score, timeout=1800)

            # Select weight based on layer type
            weight_map = {
                "occupancy": occ_weight,
                "revenue":   min(revenue_density / 500.0, 1.0),  # normalise ₹/slot
                "demand":    forecast_score,
            }
            weight = weight_map.get(layer_type, occ_weight)

            heatmap_points.append({
                "lat": lot.latitude,
                "lng": lot.longitude,
                "weight": weight,
                "lot_id": str(lot.id),
                "lot_name": lot.name,
                "available": total - occupied,
                "total_slots": total,
                "occupancy_rate": round(occupancy_rate * 100, 1),
                "revenue_density": revenue_density,
                "demand_forecast_score": forecast_score,
                # Colour band for frontend
                "color_band": (
                    "green" if occupancy_rate < 0.40
                    else "yellow" if occupancy_rate < 0.70
                    else "red"
                ),
            })

        return Response(heatmap_points)


class ForecastView(APIView):
    """Get demand forecast for a specific lot."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, lot_pk):
        hours = int(request.query_params.get("hours", 24))
        cache_key = f"demand_forecast:{lot_pk}"
        forecast = cache.get(cache_key)

        if not forecast:
            forecaster = DemandForecaster()
            forecast = forecaster.predict(str(lot_pk), hours_ahead=hours)
            cache.set(cache_key, forecast, timeout=3600)

        return Response(forecast)
