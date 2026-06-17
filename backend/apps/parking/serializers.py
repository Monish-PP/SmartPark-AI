from rest_framework import serializers
from apps.parking.models import ParkingLot, ParkingSlot, ParkingSchedule, OccupancyLog


class ParkingScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSchedule
        fields = ["id", "day_of_week", "open_time", "close_time", "is_closed"]


class ParkingSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSlot
        fields = [
            "id", "slot_number", "vehicle_type", "price_per_hour",
            "is_occupied", "is_available", "occupancy_confidence", "last_detected_at",
        ]
        read_only_fields = ["id", "is_occupied", "occupancy_confidence", "last_detected_at"]


class ParkingLotSerializer(serializers.ModelSerializer):
    slots = ParkingSlotSerializer(many=True, read_only=True)
    schedules = ParkingScheduleSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    available_slots_count = serializers.SerializerMethodField()

    class Meta:
        model = ParkingLot
        fields = [
            "id", "owner", "owner_name", "name", "description", "address",
            "latitude", "longitude", "supported_vehicles", "images",
            "is_active", "is_verified", "available_slots_count",
            "slots", "schedules", "created_at",
        ]
        read_only_fields = ["id", "owner", "is_verified", "created_at"]

    def get_available_slots_count(self, obj):
        return obj.slots.filter(is_available=True, is_occupied=False).count()

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class OccupancyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OccupancyLog
        fields = ["id", "slot", "is_occupied", "confidence", "detected_at", "frame_url"]


class ParkingLotListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for search results (no nested slots)."""
    available_count = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(read_only=True, default=None)
    ai_score = serializers.FloatField(read_only=True, default=None)

    class Meta:
        model = ParkingLot
        fields = [
            "id", "name", "address", "latitude", "longitude",
            "supported_vehicles", "images", "is_verified",
            "available_count", "distance_km", "ai_score",
        ]

    def get_available_count(self, obj):
        return obj.slots.filter(is_available=True, is_occupied=False).count()
