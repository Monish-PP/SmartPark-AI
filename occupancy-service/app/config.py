"""
SmartPark AI — Edge Occupancy Service Configuration
====================================================
All settings are driven by environment variables so the
same Docker image works across development and production.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Django Backend ────────────────────────────────────────────────────────
    # Full base URL of the Django REST API (no trailing slash)
    DJANGO_API_URL: str = os.getenv("DJANGO_API_URL", "http://localhost:8000/api")

    # Shared secret placed in X-Edge-Secret header for backend auth
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "changeme-edge-secret")

    # ── Parking Lot Identity ──────────────────────────────────────────────────
    # The MongoDB ParkingLot _id / UUID this service reports for
    PARKING_ID: str = os.getenv("PARKING_ID", "P001")

    # ── Camera Source ─────────────────────────────────────────────────────────
    # "0" = default webcam, "1" = second webcam,
    # or RTSP/HTTP URL: "rtsp://user:pass@192.168.1.10:554/stream"
    CAMERA_SOURCE: str = os.getenv("CAMERA_SOURCE", "0")

    # ── Detection Settings ────────────────────────────────────────────────────
    # Seconds between full detection cycles (1 = real-time)
    DETECTION_INTERVAL_SEC: float = float(os.getenv("DETECTION_INTERVAL_SEC", "1.0"))

    # YOLOv8 confidence threshold (0.0–1.0)
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))

    # Frames a slot must be consistently occupied/free before state flips
    # (hysteresis to prevent noise-induced flapping)
    HYSTERESIS_FRAMES: int = int(os.getenv("HYSTERESIS_FRAMES", "3"))

    # Total number of parking slots managed by this camera
    TOTAL_PARKING_SLOTS: int = int(os.getenv("TOTAL_PARKING_SLOTS", "20"))

    # YOLO COCO class IDs to count as "vehicle present"
    # 2=car, 3=motorcycle, 5=bus, 7=truck
    VEHICLE_CLASS_IDS: list[int] = json.loads(
        os.getenv("VEHICLE_CLASS_IDS", "[2, 3, 5, 7]")
    )

    # ── Slot Region Mapping ───────────────────────────────────────────────────
    # JSON array of slot bounding boxes in the camera frame:
    # [[x1, y1, x2, y2, "slot_id"], ...]
    # If null/empty → count total vehicles as proxy for occupancy
    _raw_regions = os.getenv("SLOT_REGIONS_JSON", "")
    SLOT_REGIONS: list = json.loads(_raw_regions) if _raw_regions.strip() else []

    # ── Backend Reporting ─────────────────────────────────────────────────────
    # Only POST an update if occupancy changed by at least this many slots
    MIN_CHANGE_TO_REPORT: int = int(os.getenv("MIN_CHANGE_TO_REPORT", "0"))

    # Retry settings for failed backend POSTs
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_SEC: float = float(os.getenv("RETRY_BACKOFF_SEC", "2.0"))

    # ── Service ───────────────────────────────────────────────────────────────
    SERVICE_HOST: str = os.getenv("SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8001"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
