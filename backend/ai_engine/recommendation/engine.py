"""
SmartPark AI — Parking Recommendation Engine
=============================================
Uses an ensemble of:
  - KNN (neighbour-based filtering)
  - Random Forest (feature importance-based scoring)
  - XGBoost (gradient boosting for final ranking)

Trained on PKLot-derived features + historical booking data.
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
import joblib
import logging
from pathlib import Path
from geopy.distance import geodesic
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class ParkingRecommender:
    """
    AI-powered parking recommendation engine.

    Scoring factors:
      1. Distance from user location
      2. Vehicle type compatibility
      3. Current occupancy rate (from YOLOv8 detection)
      4. Price per hour
      5. Available slot count
      6. Historical demand at this hour
      7. User review rating average
    """

    FEATURE_COLS = [
        "distance_km",
        "occupancy_rate",
        "price_per_hour",
        "available_slots",
        "avg_rating",
        "demand_score",
        "duration_fit",          # 1 if duration matches historical avg, else 0
    ]

    def __init__(self):
        self.scaler = MinMaxScaler()
        self.rf_model = None
        self.xgb_model = None
        self._load_models()

    def _load_models(self):
        """Load pre-trained models if they exist."""
        model_path = Path(settings.ML_MODELS_DIR)
        rf_path = model_path / "recommender_rf.pkl"
        xgb_path = model_path / "recommender_xgb.pkl"
        scaler_path = model_path / "recommender_scaler.pkl"

        if rf_path.exists():
            self.rf_model = joblib.load(rf_path)
            logger.info("Loaded Random Forest recommender model.")
        if xgb_path.exists():
            self.xgb_model = joblib.load(xgb_path)
            logger.info("Loaded XGBoost recommender model.")
        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)

    def _get_candidate_lots(self, vehicle_type: str, user_lat: float, user_lng: float,
                            radius_km: float = 10.0):
        """Fetch parking lots compatible with the vehicle and within radius."""
        from apps.parking.models import ParkingLot

        lots = ParkingLot.objects.filter(
            is_active=True,
            is_verified=True,
        ).prefetch_related("slots", "bookings")

        candidates = []
        for lot in lots:
            # Vehicle type filter
            if vehicle_type not in (lot.supported_vehicles or []):
                continue

            # Available slot check
            avail_slots = lot.slots.filter(
                vehicle_type=vehicle_type,
                is_available=True,
                is_occupied=False,
            )
            if not avail_slots.exists():
                continue

            # Distance filter
            dist = geodesic((user_lat, user_lng), (lot.latitude, lot.longitude)).km
            if dist > radius_km:
                continue

            candidates.append((lot, avail_slots, dist))

        return candidates

    def _build_feature_matrix(self, candidates, duration_hours: float) -> pd.DataFrame:
        """Convert candidate lots into a feature DataFrame."""
        from apps.bookings.models import Booking
        rows = []
        now = timezone.now()

        for lot, avail_slots, dist in candidates:
            total_slots = lot.slots.filter(vehicle_type=avail_slots.first().vehicle_type).count()
            occupied = total_slots - avail_slots.count()
            occupancy_rate = occupied / total_slots if total_slots > 0 else 0

            # Average price of compatible available slots
            avg_price = float(avail_slots.aggregate(
                avg=__import__('django.db.models', fromlist=['Avg']).Avg('price_per_hour')
            )["avg"] or 0)

            # Avg review rating
            from apps.bookings.models import BookingReview
            reviews = BookingReview.objects.filter(
                booking__slot__lot=lot
            ).values_list("rating", flat=True)
            avg_rating = float(np.mean(list(reviews))) if reviews else 3.0

            # Demand score: bookings in last 2 hours
            recent_bookings = Booking.objects.filter(
                slot__lot=lot,
                created_at__gte=now - __import__('datetime').timedelta(hours=2),
            ).count()
            demand_score = min(recent_bookings / 10.0, 1.0)

            # Duration fit: average booking duration at this lot vs requested
            completed_bookings = Booking.objects.filter(
                slot__lot=lot, status="completed",
                actual_entry__isnull=False, actual_exit__isnull=False,
            )
            if completed_bookings.exists():
                avg_duration = np.mean([
                    (b.actual_exit - b.actual_entry).total_seconds() / 3600
                    for b in completed_bookings
                ])
                duration_fit = 1.0 - min(abs(avg_duration - duration_hours) / 4.0, 1.0)
            else:
                duration_fit = 0.5

            rows.append({
                "lot_id": str(lot.id),
                "lot_name": lot.name,
                "address": lot.address,
                "latitude": lot.latitude,
                "longitude": lot.longitude,
                "best_slot_id": str(avail_slots.order_by("price_per_hour").first().id),
                "price_per_hour": avg_price,
                "distance_km": dist,
                "occupancy_rate": occupancy_rate,
                "available_slots": avail_slots.count(),
                "avg_rating": avg_rating,
                "demand_score": demand_score,
                "duration_fit": duration_fit,
            })

        return pd.DataFrame(rows)

    def _rule_based_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Weighted scoring when no trained model is available.

        Updated weights for edge-computing occupancy integration:
          40% Duration Match    — park where you'll fit the full duration
          20% Distance          — closer is better
          15% Occupancy Signal  — prefer lots with lower occupancy
          10% Available Slots   — more available = safer bet
          10% Price             — cheaper is better
           5% Ratings           — user satisfaction
        """
        weights = {
            "duration_fit":     +0.40,   # higher fit = better
            "distance_km":      -0.20,   # closer is better (negative = penalise far)
            "occupancy_rate":   -0.15,   # lower occupancy = better
            "available_slots":  +0.10,   # more available = better
            "price_per_hour":   -0.10,   # cheaper is better
            "avg_rating":       +0.05,   # higher rating = better
            "demand_score":     -0.00,   # not used in primary scoring
        }
        scaled = self.scaler.fit_transform(df[self.FEATURE_COLS])
        scaled_df = pd.DataFrame(scaled, columns=self.FEATURE_COLS)

        score = sum(scaled_df[col] * w for col, w in weights.items())
        return score.values

    def recommend(self, vehicle_type: str, user_lat: float, user_lng: float,
                  duration_hours: float = 1.0, top_n: int = 10) -> list:
        """
        Main recommendation method.

        Hard rejection rules (applied before scoring):
          - No available slots → reject.
          - Vehicle type not supported → reject.
          - Occupancy rate >= 100% (full lot) → reject.

        Returns list of ranked parking lots with AI score and best slot.
        """
        candidates = self._get_candidate_lots(vehicle_type, user_lat, user_lng)
        if not candidates:
            return []

        df = self._build_feature_matrix(candidates, duration_hours)
        if df.empty:
            return []

        # ── Hard rejection rules ─────────────────────────────────────────────
        before = len(df)
        df = df[
            (df["available_slots"] > 0) &           # must have free slots
            (df["occupancy_rate"] < 1.0)             # must not be 100% full
        ]
        rejected = before - len(df)
        if rejected:
            logger.info(f"Rejected {rejected} lot(s) due to no availability.")
        if df.empty:
            return []

        # Use XGBoost if available, else Random Forest, else rule-based
        if self.xgb_model is not None:
            X = self.scaler.transform(df[self.FEATURE_COLS])
            scores = self.xgb_model.predict(X)
        elif self.rf_model is not None:
            X = self.scaler.transform(df[self.FEATURE_COLS])
            scores = self.rf_model.predict(X)
        else:
            scores = self._rule_based_score(df)

        df["ai_score"] = scores
        df = df.sort_values("ai_score", ascending=False).head(top_n)

        return df[[
            "lot_id", "lot_name", "address", "latitude", "longitude",
            "best_slot_id", "price_per_hour", "distance_km",
            "available_slots", "occupancy_rate", "avg_rating", "ai_score",
        ]].to_dict(orient="records")


# ── Training Script ────────────────────────────────────────────────────────────
def train_recommender(booking_df: pd.DataFrame, save_dir: str = "ml_models"):
    """
    Train XGBoost recommender on historical booking data.
    booking_df must contain: FEATURE_COLS + 'label' (1=good choice, 0=bad)

    Usage:
        import pandas as pd
        from ai_engine.recommendation.engine import train_recommender
        df = pd.read_csv("historical_bookings.csv")
        train_recommender(df)
    """
    import os
    os.makedirs(save_dir, exist_ok=True)

    feature_cols = ParkingRecommender.FEATURE_COLS
    X = booking_df[feature_cols]
    y = booking_df["label"]

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Random Forest
    rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
    rf.fit(X_scaled, y)

    # XGBoost
    xgb_model = xgb.XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    xgb_model.fit(X_scaled, y)

    joblib.dump(scaler,     f"{save_dir}/recommender_scaler.pkl")
    joblib.dump(rf,         f"{save_dir}/recommender_rf.pkl")
    joblib.dump(xgb_model,  f"{save_dir}/recommender_xgb.pkl")

    logger.info("Recommender models trained and saved.")
    return {"rf_score": rf.score(X_scaled, y), "xgb_score": xgb_model.score(X_scaled, y)}
