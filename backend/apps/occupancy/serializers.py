"""
SmartPark AI — Occupancy Serializers
"""

from rest_framework import serializers
from apps.occupancy.models import OccupancySnapshot, OccupancyHistory
from django.utils.dateparse import parse_datetime


class OccupancyUpdateSerializer(serializers.Serializer):
    """
    Validates the payload sent by the edge occupancy-service.
    """

    parking_id = serializers.CharField(max_length=100)
    total_slots = serializers.IntegerField(min_value=0)
    occupied_slots = serializers.IntegerField(min_value=0)
    available_slots = serializers.IntegerField(min_value=0)
    occupancy_rate = serializers.FloatField(min_value=0.0, max_value=100.0)
    slot_states = serializers.DictField(
        child=serializers.BooleanField(),
        required=False,
        default=dict,
    )
    timestamp = serializers.CharField()   # ISO datetime string

    def validate_timestamp(self, value):
        dt = parse_datetime(value)
        if dt is None:
            raise serializers.ValidationError("Invalid ISO datetime string.")
        return dt

    def validate(self, data):
        if data["occupied_slots"] + data["available_slots"] != data["total_slots"]:
            # Auto-correct if there's a rounding mismatch
            data["available_slots"] = data["total_slots"] - data["occupied_slots"]
        return data


class OccupancySnapshotSerializer(serializers.ModelSerializer):
    parking_lot_id = serializers.UUIDField(source="parking_lot.id", read_only=True)
    parking_lot_name = serializers.CharField(source="parking_lot.name", read_only=True)
    parking_lot_lat = serializers.FloatField(source="parking_lot.latitude", read_only=True)
    parking_lot_lng = serializers.FloatField(source="parking_lot.longitude", read_only=True)

    class Meta:
        model = OccupancySnapshot
        fields = [
            "id",
            "parking_lot_id",
            "parking_lot_name",
            "parking_lot_lat",
            "parking_lot_lng",
            "total_slots",
            "occupied_slots",
            "available_slots",
            "occupancy_rate",
            "slot_states",
            "source",
            "edge_timestamp",
            "received_at",
        ]


class OccupancyHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OccupancyHistory
        fields = [
            "id",
            "total_slots",
            "occupied_slots",
            "available_slots",
            "occupancy_rate",
            "recorded_at",
        ]
