"""
SmartPark AI — Occupancy Models
=================================
Two models:
  OccupancySnapshot  — latest occupancy state per parking lot (upserted on each update)
  OccupancyHistory   — append-only time-series log for trend charts
"""

import uuid
from django.db import models
from apps.parking.models import ParkingLot


class OccupancySnapshot(models.Model):
    """
    Latest occupancy snapshot for a parking lot, updated by the edge service.
    One record per parking lot (upserted via update_or_create).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parking_lot = models.OneToOneField(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name="occupancy_snapshot",
    )

    # Aggregate counts (from edge service report)
    total_slots = models.IntegerField(default=0)
    occupied_slots = models.IntegerField(default=0)
    available_slots = models.IntegerField(default=0)

    # Percentage 0–100
    occupancy_rate = models.FloatField(default=0.0)

    # Per-slot state map: {"S1": true, "S2": false, ...}
    slot_states = models.JSONField(default=dict)

    # Who updated this record
    SOURCE_CHOICES = [
        ("edge_ai", "Edge AI Service"),
        ("manual", "Manual Override"),
        ("simulation", "Simulation"),
    ]
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="edge_ai")

    # Timestamps
    edge_timestamp = models.DateTimeField(
        help_text="Timestamp from the edge service payload"
    )
    received_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Occupancy Snapshot"
        verbose_name_plural = "Occupancy Snapshots"

    def __str__(self):
        return (
            f"{self.parking_lot.name} — "
            f"{self.occupied_slots}/{self.total_slots} "
            f"({self.occupancy_rate:.1f}%)"
        )


class OccupancyHistory(models.Model):
    """
    Append-only time-series of occupancy snapshots.
    Written on every edge service update — used for trend charts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parking_lot = models.ForeignKey(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name="occupancy_history",
    )

    total_slots = models.IntegerField()
    occupied_slots = models.IntegerField()
    available_slots = models.IntegerField()
    occupancy_rate = models.FloatField()

    # Edge-reported timestamp (from payload)
    recorded_at = models.DateTimeField(
        help_text="Timestamp reported by the edge service"
    )

    class Meta:
        verbose_name = "Occupancy History"
        verbose_name_plural = "Occupancy History"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["parking_lot", "-recorded_at"]),
        ]

    def __str__(self):
        return (
            f"{self.parking_lot.name} @ {self.recorded_at} — "
            f"{self.occupied_slots}/{self.total_slots}"
        )
