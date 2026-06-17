"""
SmartPark AI — Real-time Occupancy Detector
============================================
Uses YOLOv8 (ultralytics) + OpenCV to detect occupied/vacant
parking slots from CCTV frames.

Trained on the PKLot dataset:
  - Classes: 0 = empty, 1 = occupied
  - Input: camera frame (jpg/png or video stream)
  - Output: per-slot occupancy with confidence score

YOLOv8 model fine-tuned on PKLot can be downloaded from:
  https://universe.roboflow.com/brad-dwyer/pklot-1tros
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("ultralytics not installed. YOLOv8 detection disabled.")


class ParkingOccupancyDetector:
    """
    Real-time parking occupancy detection pipeline.

    Usage:
        detector = ParkingOccupancyDetector()
        results = detector.detect_from_url("http://camera-feed-url/snapshot.jpg")
        # results: [{"slot_id": "A1", "is_occupied": True, "confidence": 0.92}]
    """

    # PKLot class labels
    EMPTY_CLASS = 0
    OCCUPIED_CLASS = 1
    CLASS_NAMES = {0: "empty", 1: "occupied"}
    CONFIDENCE_THRESHOLD = 0.45

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        model_path = Path(settings.YOLO_MODEL_PATH)
        if not YOLO_AVAILABLE:
            return

        if model_path.exists():
            self.model = YOLO(str(model_path))
            logger.info(f"YOLOv8 model loaded from {model_path}")
        else:
            # Download pretrained YOLOv8n as fallback
            logger.warning("Custom YOLO model not found. Loading YOLOv8n base model.")
            self.model = YOLO("yolov8n.pt")

    def detect_from_frame(self, frame: np.ndarray, slot_regions: list = None) -> list:
        """
        Run YOLOv8 inference on a single frame.

        Args:
            frame: BGR numpy array from OpenCV
            slot_regions: Optional list of bounding boxes [(x1,y1,x2,y2, slot_id)]
                         If None, auto-detect all parking regions.

        Returns:
            List of dicts: {slot_id, is_occupied, confidence, bbox}
        """
        if self.model is None:
            return self._mock_detection(frame)

        results = self.model(frame, conf=self.CONFIDENCE_THRESHOLD, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # If slot_regions provided, map detection to closest slot
                slot_id = self._match_slot(x1, y1, x2, y2, slot_regions)

                detections.append({
                    "slot_id": slot_id,
                    "is_occupied": cls_id == self.OCCUPIED_CLASS,
                    "confidence": round(conf, 3),
                    "class_name": self.CLASS_NAMES.get(cls_id, "unknown"),
                    "bbox": [x1, y1, x2, y2],
                })

        return detections

    def detect_from_url(self, url: str, slot_regions: list = None) -> list:
        """Fetch frame from URL and run detection."""
        cap = cv2.VideoCapture(url)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            logger.error(f"Failed to capture frame from {url}")
            return []

        return self.detect_from_frame(frame, slot_regions)

    def detect_from_file(self, image_path: str, slot_regions: list = None) -> list:
        """Run detection on a local image file."""
        frame = cv2.imread(image_path)
        if frame is None:
            logger.error(f"Cannot read image at {image_path}")
            return []
        return self.detect_from_frame(frame, slot_regions)

    def process_video_stream(self, stream_url: str, slot_regions: list,
                              callback=None, max_frames: int = None):
        """
        Process a continuous video stream.
        Calls callback(detections) for each frame.
        Used by Celery periodic task.
        """
        cap = cv2.VideoCapture(stream_url)
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            detections = self.detect_from_frame(frame, slot_regions)
            if callback:
                callback(detections)

            frame_count += 1
            if max_frames and frame_count >= max_frames:
                break

        cap.release()

    def _match_slot(self, x1: int, y1: int, x2: int, y2: int,
                    slot_regions: list) -> Optional[str]:
        """Match a detection bounding box to the closest defined slot region."""
        if not slot_regions:
            return None

        det_cx = (x1 + x2) / 2
        det_cy = (y1 + y2) / 2
        best_slot = None
        best_iou = 0

        for region in slot_regions:
            rx1, ry1, rx2, ry2, slot_id = region
            iou = self._iou(x1, y1, x2, y2, rx1, ry1, rx2, ry2)
            if iou > best_iou:
                best_iou = iou
                best_slot = slot_id

        return best_slot

    @staticmethod
    def _iou(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2) -> float:
        """Compute Intersection over Union of two bounding boxes."""
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        union = area_a + area_b - inter

        return inter / union if union > 0 else 0

    def _mock_detection(self, frame: np.ndarray) -> list:
        """Fallback when YOLOv8 is not available: random simulation."""
        import random
        return [{"slot_id": None, "is_occupied": random.choice([True, False]),
                 "confidence": round(random.uniform(0.5, 0.99), 3),
                 "class_name": "mock", "bbox": [0, 0, 100, 100]}]

    def annotate_frame(self, frame: np.ndarray, detections: list) -> np.ndarray:
        """Draw bounding boxes and labels on frame for visualisation."""
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            color = (0, 0, 255) if det["is_occupied"] else (0, 255, 0)
            label = f"{'OCC' if det['is_occupied'] else 'FREE'} {det['confidence']:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return frame
