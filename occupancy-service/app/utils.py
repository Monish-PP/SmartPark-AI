"""
SmartPark AI — Edge Utility Functions
======================================
Shared helpers: logging setup, timestamp, frame annotation.
"""

import logging
import sys
from datetime import datetime, timezone

import cv2
import numpy as np


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured logging for the edge service."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("occupancy_service")


logger = setup_logging()


def utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def annotate_frame(
    frame: np.ndarray,
    detections: list[dict],
    slot_states: dict[str, bool],
    occupied_count: int,
    total_slots: int,
) -> np.ndarray:
    """
    Draw detection bounding boxes and slot status on a frame.
    Used for local preview/debugging only — frame is never transmitted.

    Args:
        frame: BGR numpy array.
        detections: list of {bbox: [x1,y1,x2,y2], class_name, confidence}.
        slot_states: dict {slot_id: is_occupied}.
        occupied_count: current occupied count.
        total_slots: total managed slots.

    Returns:
        Annotated BGR numpy array.
    """
    annotated = frame.copy()
    height, width = annotated.shape[:2]

    # Draw vehicle detections
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        color = (0, 0, 220)  # Red for vehicles
        label = f"{det['class_name']} {det['confidence']:.2f}"
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        # Label background
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(annotated, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(
            annotated, label, (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )

    # Draw slot regions
    for slot_id, is_occ in slot_states.items():
        color = (0, 60, 220) if is_occ else (0, 200, 60)
        cv2.putText(
            annotated, f"[{slot_id}]{'OCC' if is_occ else 'FREE'}",
            (10, 30 + list(slot_states.keys()).index(slot_id) * 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
        )

    # Overlay summary
    occ_rate = (occupied_count / total_slots * 100) if total_slots else 0
    summary = f"Occupied: {occupied_count}/{total_slots}  ({occ_rate:.0f}%)"
    cv2.rectangle(annotated, (0, height - 36), (width, height), (0, 0, 0), -1)
    cv2.putText(
        annotated, summary, (10, height - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
    )

    return annotated


def camera_source(raw: str):
    """
    Convert camera source string to the correct OpenCV argument.
    "0", "1", ... → int (webcam index)
    "rtsp://..." or "http://..." → str (URL)
    """
    if raw.isdigit():
        return int(raw)
    return raw


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a float between lo and hi."""
    return max(lo, min(hi, value))
