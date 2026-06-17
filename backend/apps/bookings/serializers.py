from rest_framework import serializers
from apps.bookings.models import Booking, BookingReview
from apps.parking.serializers import ParkingSlotSerializer
from apps.users.serializers import VehicleSerializer


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id", "vehicle", "slot",
            "scheduled_start", "scheduled_end",
            "estimated_amount", "ai_score", "distance_km",
        ]
        read_only_fields = ["id", "estimated_amount"]

    def validate(self, data):
        slot = data["slot"]
        vehicle = data["vehicle"]
        start = data["scheduled_start"]
        end = data["scheduled_end"]

        if end <= start:
            raise serializers.ValidationError("End time must be after start time.")

        # Vehicle type compatibility check
        if vehicle.vehicle_type != slot.vehicle_type:
            raise serializers.ValidationError(
                f"Vehicle type '{vehicle.vehicle_type}' is not compatible "
                f"with slot type '{slot.vehicle_type}'."
            )

        # Slot availability check
        if slot.is_occupied or not slot.is_available:
            raise serializers.ValidationError("This slot is not currently available.")

        # Overlapping booking check
        conflict = Booking.objects.filter(
            slot=slot,
            status__in=["pending", "confirmed", "active"],
            scheduled_start__lt=end,
            scheduled_end__gt=start,
        ).exists()
        if conflict:
            raise serializers.ValidationError("Slot is already booked for this time window.")

        # Compute estimated amount
        duration_hours = (end - start).total_seconds() / 3600
        data["estimated_amount"] = round(float(slot.price_per_hour) * duration_hours, 2)
        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class BookingSerializer(serializers.ModelSerializer):
    slot = ParkingSlotSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "user", "vehicle", "slot", "status",
            "scheduled_start", "scheduled_end",
            "actual_entry", "actual_exit",
            "estimated_amount", "final_amount", "refund_amount",
            "ai_score", "distance_km",
            "razorpay_order_id", "razorpay_payment_id", "is_paid",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class BookingReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingReview
        fields = ["id", "booking", "rating", "comment", "created_at"]
        read_only_fields = ["id", "created_at"]
