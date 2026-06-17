from django.db import models
import uuid
from apps.users.models import User


class ParkingLot(models.Model):
    """A physical parking facility owned by an OWNER."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parking_lots")

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()

    # Supported vehicle types (stored as comma-separated or JSON)
    supported_vehicles = models.JSONField(default=list)   # ["two_wheeler","four_wheeler"]

    # Real-time CCTV / Camera feed URL for occupancy detection
    camera_feed_url = models.URLField(blank=True)

    # Supabase image URLs
    images = models.JSONField(default=list)

    # Denormalised occupancy cache — updated by OccupancyUpdateView on each edge report
    # Avoids joining OccupancySnapshot on every list query
    total_slots_cache = models.IntegerField(default=0)
    occupied_slots_cache = models.IntegerField(default=0)
    occupancy_rate_cache = models.FloatField(default=0.0)   # 0.0 – 1.0
    last_occupancy_update = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} — {self.address}"


class ParkingSlot(models.Model):
    """Individual parking slot within a lot."""

    TWO_WHEELER = "two_wheeler"
    FOUR_WHEELER = "four_wheeler"
    HEAVY = "heavy"
    TYPE_CHOICES = [
        (TWO_WHEELER, "Two Wheeler"),
        (FOUR_WHEELER, "Four Wheeler"),
        (HEAVY, "Heavy Vehicle"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name="slots")
    slot_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Pricing (₹ per hour)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)

    is_occupied = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)

    # YOLO detected occupancy confidence score (0–1)
    occupancy_confidence = models.FloatField(default=0.0)
    last_detected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("lot", "slot_number")

    def __str__(self):
        return f"Slot {self.slot_number} [{self.vehicle_type}] — {self.lot.name}"


class ParkingSchedule(models.Model):
    """Availability schedule per day-of-week for a parking lot."""

    DAYS = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
        (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]

    lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.IntegerField(choices=DAYS)
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("lot", "day_of_week")

    def __str__(self):
        return f"{self.lot.name} — Day {self.day_of_week}"


class OccupancyLog(models.Model):
    """Timestamped occupancy snapshots from YOLOv8 detection."""

    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name="occupancy_logs")
    is_occupied = models.BooleanField()
    confidence = models.FloatField()
    detected_at = models.DateTimeField(auto_now_add=True)
    frame_url = models.URLField(blank=True)   # Supabase stored frame

    def __str__(self):
        return f"Slot {self.slot.slot_number} — {'Occupied' if self.is_occupied else 'Free'} @ {self.detected_at}"
