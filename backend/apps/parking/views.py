from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from apps.parking.models import ParkingLot, ParkingSlot, OccupancyLog
from apps.parking.serializers import (
    ParkingLotSerializer, ParkingSlotSerializer,
    ParkingLotListSerializer, OccupancyLogSerializer,
)
from ai_engine.recommendation.engine import ParkingRecommender


class ParkingLotListCreateView(generics.ListCreateAPIView):
    """Owner: list/create their lots. Public: list all active verified lots."""

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_active", "is_verified"]
    search_fields = ["name", "address"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ParkingLotListSerializer
        return ParkingLotSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == "owner":
            return ParkingLot.objects.filter(owner=user)
        return ParkingLot.objects.filter(is_active=True, is_verified=True)

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class ParkingLotDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ParkingLotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated and getattr(user, "role", None) == "admin":
            return ParkingLot.objects.all()
        if user and user.is_authenticated:
            return ParkingLot.objects.filter(owner=user)
        return ParkingLot.objects.none()


class ParkingSearchView(APIView):
    """
    AI-powered parking search endpoint.
    Query params: vehicle_type, lat, lng, duration_hours, max_results
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vehicle_type = request.query_params.get("vehicle_type")
        lat = float(request.query_params.get("lat", 0))
        lng = float(request.query_params.get("lng", 0))
        duration = float(request.query_params.get("duration_hours", 1))
        max_results = int(request.query_params.get("max_results", 10))

        if not vehicle_type:
            return Response(
                {"detail": "vehicle_type is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        recommender = ParkingRecommender()
        results = recommender.recommend(
            vehicle_type=vehicle_type,
            user_lat=lat,
            user_lng=lng,
            duration_hours=duration,
            top_n=max_results,
        )
        return Response(results)


class SlotListCreateView(generics.ListCreateAPIView):
    serializer_class = ParkingSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        lot_id = self.kwargs["lot_pk"]
        return ParkingSlot.objects.filter(lot_id=lot_id)

    def perform_create(self, serializer):
        lot_id = self.kwargs["lot_pk"]
        serializer.save(lot_id=lot_id)


class OccupancyStatusView(APIView):
    """Returns live occupancy for all slots in a lot."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, lot_pk):
        slots = ParkingSlot.objects.filter(lot_id=lot_pk).values(
            "id", "slot_number", "vehicle_type", "is_occupied",
            "occupancy_confidence", "last_detected_at",
        )
        return Response(list(slots))
