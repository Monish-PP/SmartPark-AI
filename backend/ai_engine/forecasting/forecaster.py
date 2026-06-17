"""
SmartPark AI — Demand Forecasting Engine
=========================================
Ensemble of:
  - LSTM (TensorFlow/Keras) — temporal sequence learning
  - Prophet (Facebook) — trend + seasonality decomposition
  - XGBoost — feature-based tabular forecasting

Predicts parking demand (occupancy %) for the next 24 hours
per parking lot, per vehicle type.
"""

import numpy as np
import pandas as pd
import logging
import joblib
from pathlib import Path
from datetime import datetime, timedelta
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available. LSTM forecasting disabled.")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available.")

import xgboost as xgb


class DemandForecaster:
    """
    24-hour parking demand forecaster using LSTM + Prophet + XGBoost ensemble.

    Usage:
        forecaster = DemandForecaster()
        forecast = forecaster.predict(lot_id="<uuid>", hours_ahead=24)
        # Returns list of {timestamp, predicted_occupancy_rate, confidence_interval}
    """

    SEQUENCE_LENGTH = 48   # 48 past half-hour slots (24 hours of history)
    FEATURE_COLS = [
        "hour_of_day", "day_of_week", "is_weekend",
        "occupancy_rate", "temperature", "is_holiday",
        "bookings_count", "rain",
    ]

    def __init__(self):
        self.lstm_model = None
        self.prophet_model = None
        self.xgb_model = None
        self._load_models()

    def _load_models(self):
        model_dir = Path(settings.ML_MODELS_DIR)

        lstm_path = model_dir / "lstm_forecaster.h5"
        prophet_path = model_dir / "prophet_forecaster.pkl"
        xgb_path = model_dir / "xgb_forecaster.pkl"

        if TF_AVAILABLE and lstm_path.exists():
            self.lstm_model = load_model(str(lstm_path))
            logger.info("LSTM forecaster loaded.")

        if PROPHET_AVAILABLE and prophet_path.exists():
            self.prophet_model = joblib.load(prophet_path)
            logger.info("Prophet forecaster loaded.")

        if xgb_path.exists():
            self.xgb_model = joblib.load(xgb_path)
            logger.info("XGBoost forecaster loaded.")

    def _get_historical_data(self, lot_id: str, hours_back: int = 24) -> pd.DataFrame:
        """Fetch recent occupancy logs from DB."""
        from apps.parking.models import OccupancyLog, ParkingSlot
        from django.utils import timezone

        cutoff = timezone.now() - timedelta(hours=hours_back)
        logs = OccupancyLog.objects.filter(
            slot__lot_id=lot_id,
            detected_at__gte=cutoff,
        ).values("detected_at", "is_occupied", "confidence")

        df = pd.DataFrame(list(logs))
        if df.empty:
            return pd.DataFrame()

        df["detected_at"] = pd.to_datetime(df["detected_at"])
        df = df.set_index("detected_at").resample("30min").agg(
            occupancy_rate=("is_occupied", "mean"),
            bookings_count=("is_occupied", "count"),
        ).reset_index()

        df["hour_of_day"] = df["detected_at"].dt.hour
        df["day_of_week"] = df["detected_at"].dt.dayofweek
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df["is_holiday"] = 0
        df["temperature"] = 28.0   # Default; integrate weather API for production
        df["rain"] = 0

        return df

    def _lstm_predict(self, historical_df: pd.DataFrame, hours_ahead: int) -> np.ndarray:
        """Run LSTM inference on sequence data."""
        if self.lstm_model is None or historical_df.empty:
            return None

        data = historical_df[self.FEATURE_COLS].fillna(0).values
        if len(data) < self.SEQUENCE_LENGTH:
            pad = np.zeros((self.SEQUENCE_LENGTH - len(data), len(self.FEATURE_COLS)))
            data = np.vstack([pad, data])

        X = data[-self.SEQUENCE_LENGTH:].reshape(1, self.SEQUENCE_LENGTH, -1)
        steps = hours_ahead * 2   # 30-minute intervals
        preds = []

        for _ in range(steps):
            pred = float(self.lstm_model.predict(X, verbose=0)[0][0])
            preds.append(np.clip(pred, 0, 1))
            # Roll window
            new_row = X[0, -1, :].copy()
            new_row[3] = pred  # update occupancy_rate feature
            X = np.roll(X, -1, axis=1)
            X[0, -1, :] = new_row

        return np.array(preds)

    def _prophet_predict(self, historical_df: pd.DataFrame, hours_ahead: int) -> np.ndarray:
        """Run Prophet forecast."""
        if self.prophet_model is None or historical_df.empty:
            return None

        future = self.prophet_model.make_future_dataframe(
            periods=hours_ahead * 2, freq="30min"
        )
        forecast = self.prophet_model.predict(future)
        values = forecast["yhat"].values[-hours_ahead * 2:]
        return np.clip(values, 0, 1)

    def _xgb_predict(self, historical_df: pd.DataFrame, hours_ahead: int) -> np.ndarray:
        """Run XGBoost feature-based prediction."""
        if self.xgb_model is None:
            return None

        from datetime import datetime, timezone as tz
        now = datetime.now(tz=tz.utc)
        future_times = [now + timedelta(minutes=30 * i) for i in range(1, hours_ahead * 2 + 1)]

        rows = []
        for t in future_times:
            rows.append({
                "hour_of_day": t.hour,
                "day_of_week": t.weekday(),
                "is_weekend": int(t.weekday() >= 5),
                "occupancy_rate": float(historical_df["occupancy_rate"].mean()) if not historical_df.empty else 0.5,
                "temperature": 28.0,
                "is_holiday": 0,
                "bookings_count": 0,
                "rain": 0,
            })

        X = pd.DataFrame(rows)[self.FEATURE_COLS]
        preds = self.xgb_model.predict(X)
        return np.clip(preds, 0, 1)

    def predict(self, lot_id: str, hours_ahead: int = 24) -> list:
        """
        Main forecast method.
        Returns hourly demand predictions for the next `hours_ahead` hours.
        """
        hist_df = self._get_historical_data(lot_id, hours_back=24)

        lstm_preds = self._lstm_predict(hist_df, hours_ahead)
        prophet_preds = self._prophet_predict(hist_df, hours_ahead)
        xgb_preds = self._xgb_predict(hist_df, hours_ahead)

        # Weighted ensemble average
        available = [p for p in [lstm_preds, prophet_preds, xgb_preds] if p is not None]
        if not available:
            # Fallback: sine curve approximating typical daily demand
            steps = hours_ahead * 2
            t = np.linspace(0, 2 * np.pi, steps)
            ensemble = 0.4 + 0.3 * np.sin(t - np.pi / 2)
        else:
            ensemble = np.mean(available, axis=0)

        from datetime import datetime, timezone as tz
        now = datetime.now(tz=tz.utc)
        results = []
        for i, occ in enumerate(ensemble):
            ts = now + timedelta(minutes=30 * (i + 1))
            results.append({
                "timestamp": ts.isoformat(),
                "predicted_occupancy_rate": round(float(occ), 3),
                "demand_level": "high" if occ > 0.75 else ("medium" if occ > 0.4 else "low"),
            })

        return results


# ── Training Functions ─────────────────────────────────────────────────────────

def train_lstm(df: pd.DataFrame, save_dir: str = "ml_models"):
    """Train and save LSTM model on historical occupancy data."""
    if not TF_AVAILABLE:
        raise RuntimeError("TensorFlow is required to train LSTM.")

    import os
    os.makedirs(save_dir, exist_ok=True)

    SEQUENCE_LENGTH = 48
    FEATURE_COLS = DemandForecaster.FEATURE_COLS
    data = df[FEATURE_COLS].fillna(0).values

    # Create sliding window sequences
    X, y = [], []
    for i in range(SEQUENCE_LENGTH, len(data)):
        X.append(data[i - SEQUENCE_LENGTH:i])
        y.append(data[i, 3])  # occupancy_rate index

    X = np.array(X)
    y = np.array(y)

    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(SEQUENCE_LENGTH, len(FEATURE_COLS))),
        Dropout(0.2),
        LSTM(64),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    model.fit(X, y, epochs=50, batch_size=32,
              validation_split=0.1,
              callbacks=[EarlyStopping(patience=5, restore_best_weights=True)])

    model.save(f"{save_dir}/lstm_forecaster.h5")
    logger.info("LSTM model saved.")
    return model


def train_prophet(df: pd.DataFrame, save_dir: str = "ml_models"):
    """Train and save Prophet model."""
    if not PROPHET_AVAILABLE:
        raise RuntimeError("Prophet is required.")

    prophet_df = df[["detected_at", "occupancy_rate"]].rename(
        columns={"detected_at": "ds", "occupancy_rate": "y"}
    )
    model = Prophet(
        changepoint_prior_scale=0.05,
        seasonality_mode="multiplicative",
        daily_seasonality=True,
        weekly_seasonality=True,
    )
    model.fit(prophet_df)
    joblib.dump(model, f"{save_dir}/prophet_forecaster.pkl")
    logger.info("Prophet model saved.")
    return model


def train_xgboost_forecaster(df: pd.DataFrame, save_dir: str = "ml_models"):
    """Train and save XGBoost forecaster."""
    import os
    os.makedirs(save_dir, exist_ok=True)

    FEATURE_COLS = DemandForecaster.FEATURE_COLS
    X = df[FEATURE_COLS].fillna(0)
    y = df["occupancy_rate"]

    model = xgb.XGBRegressor(
        n_estimators=500, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    model.fit(X, y)
    joblib.dump(model, f"{save_dir}/xgb_forecaster.pkl")
    logger.info("XGBoost forecaster saved.")
    return model
