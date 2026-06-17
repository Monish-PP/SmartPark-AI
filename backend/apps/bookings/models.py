from django.db import models
from django.utils import timezone
import uuid
from apps.users.models import User, Vehicle
from apps.parking.models import ParkingSlot


class Booking(models.Model):
    """Core booking record with full lifecycle tracking."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"         # Vehicle has entered
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
        (REFUNDED, "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="bookings")
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name="bookings")

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=PENDING)

    # Duration window
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_entry = models.DateTimeField(null=True, blank=True)
    actual_exit = models.DateTimeField(null=True, blank=True)

    # Billing
    estimated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # AI recommendation metadata
    ai_score = models.FloatField(null=True, blank=True)         # Composite ML score
    distance_km = models.FloatField(null=True, blank=True)

    # Razorpay
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_final_amount(self):
        """Compute actual billing based on real entry/exit times."""
        if self.actual_entry and self.actual_exit:
            duration_hours = (self.actual_exit - self.actual_entry).total_seconds() / 3600
            rate = float(self.slot.price_per_hour)
            self.final_amount = round(duration_hours * rate, 2)
        return self.final_amount

    def calculate_refund(self):
        """Calculate refund for early exit (unused time)."""
        if self.final_amount and self.estimated_amount:
            diff = float(self.estimated_amount) - float(self.final_amount)
            self.refund_amount = max(0, diff)
        return self.refund_amount

    def __str__(self):
        return f"Booking {self.id} — {self.user.email} — {self.status}"


class BookingReview(models.Model):
    """Post-parking review by user."""

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for Booking {self.booking.id} — {self.rating}★"
