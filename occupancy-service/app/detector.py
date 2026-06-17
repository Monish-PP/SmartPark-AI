"""
SmartPark AI — Edge YOLOv8 Detector
=====================================
Standalone vehicle detector — no Django dependency.
Connects to webcam or IP camera, runs YOLOv8 inference locally,
returns per-frame detection results.

Camera feed is NEVER transmitted to the cloud.
Only occupancy status events leave this machine.
"""

import logging
import time
from typing import Generator

import cv2
import numpy as np

from app.config import settings
from app.utils import camera_source

logger = logging.getLogger("occupancy_service.detector")

# COCO class name lookup (subset relevant to parking)
COCO_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except ImportError:
    _YOLO_AVAILABLE = False
    logger.warning(
        "ultralytics not installed — running in MOCK mode. "
        "Install with: pip install ultralytics"
    )


class VehicleDetector:
    """
    YOLOv8-powered vehicle detector for edge occupancy detection.

    Usage:
        detector = VehicleDetector()
        for frame, detections in detector.stream():
            # detections: [{bbox, class_id, class_name, confidence}]
            process(detections)
    """

    MODEL_PATH = "models/yolov8n.pt"   # falls back to auto-download

    def __init__(self):
        self.model = None
        self.confidence = settings.CONFIDENCE_THRESHOLD
        self.vehicle_classes = set(settings.VEHICLE_CLASS_IDS)
        self._load_model()

    # ── Model Loading ─────────────────────────────────────────────────────────

    def _load_model(self) -> None:
        if not _YOLO_AVAILABLE:
            logger.warning("YOLOv8 unavailable. Using mock detector.")
            return

        try:
            self.model = YOLO(self.MODEL_PATH)
            logger.info(f"YOLOv8 model loaded: {self.MODEL_PATH}")
        except Exception as e:
            logger.warning(f"Custom model not found ({e}). Downloading YOLOv8n…")
            try:
                self.model = YOLO("yolov8n.pt")
                logger.info("YOLOv8n base model downloaded and loaded.")
            except Exception as ex:
                logger.error(f"Failed to load any YOLO model: {ex}")
                self.model = None

    # ── Single Frame Inference ────────────────────────────────────────────────

    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Run YOLOv8 inference on a single BGR frame.

        Returns list of dicts:
            {
                "bbox": [x1, y1, x2, y2],
                "class_id": int,
                "class_name": str,
                "confidence": float
            }
        Only returns detections for vehicle class IDs.
        """
        if self.model is None:
            return self._mock_detect(frame)

        try:
            results = self.model(
                frame,
                conf=self.confidence,
                verbose=False,
                classes=list(self.vehicle_classes),
            )
        except Exception as e:
            logger.error(f"YOLO inference error: {e}")
            return []

        detections = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id not in self.vehicle_classes:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "class_id": cls_id,
                    "class_name": COCO_CLASSES.get(cls_id, f"class_{cls_id}"),
                    "confidence": round(float(box.conf[0]), 3),
                })

        return detections

    # ── Camera Stream ─────────────────────────────────────────────────────────

    def stream(self) -> Generator[tuple[np.ndarray, list[dict]], None, None]:
        """
        Open camera and yield (frame, detections) continuously.
        Caller controls the loop; use `break` to stop.

        Handles camera disconnects with automatic reconnect (up to 3 attempts),
        and falls back to a mock camera generator if no device is found.
        """
        src = camera_source(settings.CAMERA_SOURCE)
        reconnect_attempts = 0
        max_reconnects = 3

        while reconnect_attempts < max_reconnects:
            logger.info(f"Opening camera: {src} (attempt {reconnect_attempts + 1})")
            cap = cv2.VideoCapture(src)

            if not cap.isOpened():
                reconnect_attempts += 1
                logger.warning(
                    f"Cannot open camera {src}. "
                    f"Retry {reconnect_attempts}/{max_reconnects} in 2s…"
                )
                time.sleep(2)
                continue

            # Set reasonable capture properties
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # minimal buffer lag
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            logger.info(f"Camera opened: {src} @ "
                        f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x"
                        f"{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            reconnect_attempts = 0  # reset on successful open

            consecutive_failures = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    consecutive_failures += 1
                    logger.warning(f"Frame read failed ({consecutive_failures}/10)")
                    if consecutive_failures >= 10:
                        logger.error("Too many read failures — reconnecting.")
                        break
                    time.sleep(0.1)
                    continue

                consecutive_failures = 0
                detections = self.detect(frame)
                yield frame, detections

            cap.release()
            reconnect_attempts += 1
            logger.info("Camera released. Reconnecting in 2s…")
            time.sleep(2)

        # Fallback to mock stream if no physical camera can be opened
        logger.warning(
            f"Unable to open camera {src} after {max_reconnects} attempts. "
            "Falling back to MOCK camera stream."
        )
        mock_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        while True:
            detections = self._mock_detect(mock_frame)
            yield mock_frame, detections
            time.sleep(settings.DETECTION_INTERVAL_SEC)

    # ── Mock Fallback ─────────────────────────────────────────────────────────

    @staticmethod
    def _mock_detect(frame: np.ndarray) -> list[dict]:
        """Return synthetic detections for testing without a camera/GPU."""
        import random
        h, w = frame.shape[:2]
        count = random.randint(0, 5)
        detections = []
        for _ in range(count):
            x1 = random.randint(0, w - 100)
            y1 = random.randint(0, h - 100)
            x2 = x1 + random.randint(60, 120)
            y2 = y1 + random.randint(50, 100)
            cls_id = random.choice([2, 3, 5, 7])
            detections.append({
                "bbox": [x1, y1, min(x2, w), min(y2, h)],
                "class_id": cls_id,
                "class_name": COCO_CLASSES.get(cls_id, "vehicle"),
                "confidence": round(random.uniform(0.5, 0.99), 3),
            })
        return detections
