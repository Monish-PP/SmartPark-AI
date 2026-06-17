"""
SmartPark AI — Slot State Manager
===================================
Maps YOLOv8 vehicle detections → parking slot occupancy states.

Two operating modes:
  1. REGION mode  — slot bounding boxes defined in SLOT_REGIONS_JSON env var.
                    IoU matching assigns each detection to a slot.
  2. COUNT mode   — no regions defined; total vehicle count is used as
                    a proxy for occupied slots (simpler, less precise).

Hysteresis prevents noise-induced state flapping: a slot must be
consistently occupied/free for HYSTERESIS_FRAMES consecutive cycles
before its reported state changes.
"""

import logging
from collections import defaultdict

from app.config import settings

logger = logging.getLogger("occupancy_service.slot_manager")


class SlotManager:
    """
    Maintains authoritative per-slot occupancy state with hysteresis.

    Public interface:
        update(detections)  → returns OccupancySummary dict
        current_summary()   → returns last OccupancySummary dict
        slot_states         → {slot_id: bool}  (True = occupied)
    """

    def __init__(self):
        self.total_slots: int = settings.TOTAL_PARKING_SLOTS
        self.hysteresis: int = settings.HYSTERESIS_FRAMES
        self.regions: list = settings.SLOT_REGIONS   # [[x1,y1,x2,y2,slot_id], ...]

        # Stable (reported) state for each slot
        self.slot_states: dict[str, bool] = {}

        # Consecutive-frame evidence counters (positive = occupied evidence)
        self._evidence: dict[str, int] = defaultdict(int)

        if self.regions:
            # Initialise all defined slots as free
            for region in self.regions:
                slot_id = str(region[4])
                self.slot_states[slot_id] = False
            logger.info(
                f"SlotManager: REGION mode — {len(self.regions)} slots configured."
            )
        else:
            # Initialise synthetic slots S1…SN
            for i in range(1, self.total_slots + 1):
                slot_id = f"S{i}"
                self.slot_states[slot_id] = False
            logger.info(
                f"SlotManager: COUNT mode — {self.total_slots} virtual slots."
            )

        self._last_summary: dict = self._build_summary()

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, detections: list[dict]) -> dict:
        """
        Process a new detection list and return the updated occupancy summary.

        Args:
            detections: list of {bbox, class_id, class_name, confidence}

        Returns:
            OccupancySummary dict:
            {
                parking_id, total_slots, occupied_slots, available_slots,
                occupancy_rate, slot_states, changed
            }
        """
        if self.regions:
            self._update_region_mode(detections)
        else:
            self._update_count_mode(detections)

        summary = self._build_summary()
        summary["changed"] = self._last_summary.get("occupied_slots") != summary["occupied_slots"]
        self._last_summary = summary
        return summary

    def current_summary(self) -> dict:
        return self._last_summary

    # ── Region Mode ───────────────────────────────────────────────────────────

    def _update_region_mode(self, detections: list[dict]) -> None:
        """
        For each defined slot region, check if any detection's bbox overlaps.
        Apply hysteresis before changing stable state.
        """
        # Build set of slot IDs that have a detection in this frame
        occupied_this_frame: set[str] = set()

        for det in detections:
            dx1, dy1, dx2, dy2 = det["bbox"]
            for region in self.regions:
                rx1, ry1, rx2, ry2, slot_id = region
                slot_id = str(slot_id)
                if self._iou(dx1, dy1, dx2, dy2, rx1, ry1, rx2, ry2) > 0.15:
                    occupied_this_frame.add(slot_id)

        # Update evidence counters and apply hysteresis
        for slot_id in self.slot_states:
            currently_occupied = slot_id in occupied_this_frame
            if currently_occupied:
                self._evidence[slot_id] = min(
                    self._evidence[slot_id] + 1, self.hysteresis
                )
            else:
                self._evidence[slot_id] = max(
                    self._evidence[slot_id] - 1, -self.hysteresis
                )

            # Flip stable state only when evidence is saturated
            if self._evidence[slot_id] >= self.hysteresis:
                self.slot_states[slot_id] = True
            elif self._evidence[slot_id] <= -self.hysteresis:
                self.slot_states[slot_id] = False

    # ── Count Mode ────────────────────────────────────────────────────────────

    def _update_count_mode(self, detections: list[dict]) -> None:
        """
        Use raw vehicle count as occupied slot count.
        Applies hysteresis via a global evidence counter.
        """
        raw_count = min(len(detections), self.total_slots)
        slot_ids = list(self.slot_states.keys())

        # Mark first `raw_count` slots as occupied with evidence
        for i, slot_id in enumerate(slot_ids):
            if i < raw_count:
                self._evidence[slot_id] = min(self._evidence[slot_id] + 1, self.hysteresis)
            else:
                self._evidence[slot_id] = max(self._evidence[slot_id] - 1, -self.hysteresis)

            if self._evidence[slot_id] >= self.hysteresis:
                self.slot_states[slot_id] = True
            elif self._evidence[slot_id] <= -self.hysteresis:
                self.slot_states[slot_id] = False

    # ── Summary Builder ───────────────────────────────────────────────────────

    def _build_summary(self) -> dict:
        occupied = sum(1 for v in self.slot_states.values() if v)
        available = self.total_slots - occupied
        rate = round((occupied / self.total_slots) * 100, 1) if self.total_slots else 0

        return {
            "parking_id": settings.PARKING_ID,
            "total_slots": self.total_slots,
            "occupied_slots": occupied,
            "available_slots": available,
            "occupancy_rate": rate,
            "slot_states": dict(self.slot_states),
            "changed": False,
        }

    # ── IoU Helper ────────────────────────────────────────────────────────────

    @staticmethod
    def _iou(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2) -> float:
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        if inter == 0:
            return 0.0
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0
