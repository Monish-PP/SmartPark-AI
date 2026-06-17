"""
SmartPark AI — Occupancy Views
================================
Three endpoints consumed by the edge service and the React frontend.

POST /api/occupancy/update/          — edge service → Django (authenticated via X-Edge-Secret)
GET  /api/occupancy/<parking_id>/    — get snapshot + 48h history for a lot
GET  /api/occupancy/all/             — get snapshots for all active lots
"""

import logging
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.occupancy.models import OccupancySnapshot, OccupancyHistory
from apps.occupancy.serializers import (
    OccupancyUpdateSerializer,
    OccupancySnapshotSerializer,
    OccupancyHistorySerializer,
)
from apps.parking.models import ParkingLot

logger = logging.getLogger(__name__)


def _publish_supabase_event(parking_lot, snapshot) -> None:
    """
    Broadcast real-time occupancy update via Supabase Broadcast channel.
    Channel name: occupancy-{parking_lot_id}
    Fires-and-forgets; errors are logged but not re-raised.
    """
    try:
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

        channel_name = f"occupancy-{str(parking_lot.id)}"
        payload = {
            "parking_id": str(parking_lot.id),
            "parking_name": parking_lot.name,
            "total_slots": snapshot.total_slots,
            "occupied_slots": snapshot.occupied_slots,
            "available_slots": snapshot.available_slots,
            "occupancy_rate": snapshot.occupancy_rate,
            "slot_states": snapshot.slot_states,
            "timestamp": snapshot.edge_timestamp.isoformat(),
        }

        # Broadcast channel — ephemeral, no DB table needed
        channel = supabase.channel(channel_name)
        channel.send_broadcast(event="occupancy_update", payload=payload)
        logger.debug(f"Supabase broadcast sent: {channel_name}")

    except ImportError:
        logger.warning("supabase-py not installed. Realtime events disabled.")
    except Exception as e:
        logger.warning(f"Supabase broadcast failed: {e}")


class OccupancyUpdateView(APIView):
    """
    POST /api/occupancy/update/

    Receives occupancy snapshot from the edge AI service.
    Authenticated via X-Edge-Secret header (not JWT — edge service has no user account).

    Actions:
      1. Validate X-Edge-Secret header.
      2. Look up ParkingLot by parking_id field.
      3. Upsert OccupancySnapshot for the lot.
      4. Append OccupancyHistory record.
      5. Bulk-update ParkingSlot.is_occupied from slot_states map.
      6. Update ParkingLot denormalised cache fields.
      7. Publish Supabase Broadcast event.
    """

    permission_classes = [AllowAny]   # Auth is via secret header, not JWT

    def post(self, request):
        # ── 1. Authenticate edge service ──────────────────────────────────────
        edge_secret = request.headers.get("X-Edge-Secret", "")
        expected_secret = getattr(settings, "EDGE_AI_SECRET", "")

        if not expected_secret or edge_secret != expected_secret:
            logger.warning(
                f"Rejected occupancy update — invalid X-Edge-Secret "
                f"from {request.META.get('REMOTE_ADDR')}"
            )
            return Response(
                {"detail": "Invalid or missing X-Edge-Secret header."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ── 2. Validate payload ───────────────────────────────────────────────
        serializer = OccupancyUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        parking_id = data["parking_id"]

        # ── 3. Resolve ParkingLot ─────────────────────────────────────────────
        try:
            parking_lot = ParkingLot.objects.get(
                id=parking_id, is_active=True
            )
        except ParkingLot.DoesNotExist:
            # Try name-based lookup as fallback
            try:
                parking_lot = ParkingLot.objects.get(
                    name__iexact=parking_id, is_active=True
                )
            except ParkingLot.DoesNotExist:
                return Response(
                    {"detail": f"ParkingLot '{parking_id}' not found or inactive."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # ── 4. Upsert OccupancySnapshot ───────────────────────────────────────
        snapshot, created = OccupancySnapshot.objects.update_or_create(
            parking_lot=parking_lot,
            defaults={
                "total_slots": data["total_slots"],
                "occupied_slots": data["occupied_slots"],
                "available_slots": data["available_slots"],
                "occupancy_rate": data["occupancy_rate"],
                "slot_states": data.get("slot_states", {}),
                "source": "edge_ai",
                "edge_timestamp": data["timestamp"],
            },
        )

        # ── 5. Append OccupancyHistory ────────────────────────────────────────
        OccupancyHistory.objects.create(
            parking_lot=parking_lot,
            total_slots=data["total_slots"],
            occupied_slots=data["occupied_slots"],
            available_slots=data["available_slots"],
            occupancy_rate=data["occupancy_rate"],
            recorded_at=data["timestamp"],
        )

        # ── 6. Update slot-level is_occupied flags ────────────────────────────
        slot_states = data.get("slot_states", {})
        if slot_states:
            from apps.parking.models import ParkingSlot
            from django.db import transaction
            with transaction.atomic():
                for slot_id_str, is_occupied in slot_states.items():
                    ParkingSlot.objects.filter(
                        lot=parking_lot,
                        slot_number=slot_id_str,
                    ).update(
                        is_occupied=is_occupied,
                        last_detected_at=data["timestamp"],
                    )

        # ── 7. Update ParkingLot denormalised cache ───────────────────────────
        ParkingLot.objects.filter(id=parking_lot.id).update(
            total_slots_cache=data["total_slots"],
            occupied_slots_cache=data["occupied_slots"],
            occupancy_rate_cache=data["occupancy_rate"] / 100.0,  # store as 0–1
            last_occupancy_update=timezone.now(),
        )

        # ── 8. Publish Supabase Realtime event ────────────────────────────────
        _publish_supabase_event(parking_lot, snapshot)

        action = "created" if created else "updated"
        logger.info(
            f"Occupancy {action}: lot={parking_lot.name} "
            f"{data['occupied_slots']}/{data['total_slots']} "
            f"({data['occupancy_rate']:.1f}%)"
        )

        return Response(
            {
                "status": "ok",
                "action": action,
                "parking_lot": str(parking_lot.id),
                "occupied_slots": data["occupied_slots"],
                "available_slots": data["available_slots"],
                "occupancy_rate": data["occupancy_rate"],
            },
            status=status.HTTP_200_OK,
        )


class OccupancyDetailView(APIView):
    """
    GET /api/occupancy/<parking_id>/

    Returns:
      - Latest OccupancySnapshot for the lot.
      - Last 48 OccupancyHistory entries (for trend charts).
    """

    permission_classes = [AllowAny]

    def get(self, request, parking_id):
        try:
            parking_lot = ParkingLot.objects.get(id=parking_id)
        except ParkingLot.DoesNotExist:
            return Response(
                {"detail": "ParkingLot not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            snapshot = parking_lot.occupancy_snapshot
            snapshot_data = OccupancySnapshotSerializer(snapshot).data
        except OccupancySnapshot.DoesNotExist:
            snapshot_data = None

        history = OccupancyHistory.objects.filter(
            parking_lot=parking_lot
        ).order_by("-recorded_at")[:48]
        history_data = OccupancyHistorySerializer(history, many=True).data

        return Response({
            "snapshot": snapshot_data,
            "history": list(reversed(history_data)),   # chronological order
        })


class OccupancyAllView(APIView):
    """
    GET /api/occupancy/all/

    Returns latest occupancy snapshot for every active, verified parking lot.
    Used by:
      - Admin Dashboard global stats.
      - Enhanced heatmap (occupancy layer).
      - User-facing search (slot availability).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        snapshots = OccupancySnapshot.objects.select_related(
            "parking_lot"
        ).filter(parking_lot__is_active=True, parking_lot__is_verified=True)

        data = OccupancySnapshotSerializer(snapshots, many=True).data

        # Aggregate platform-wide stats
        total_lots = len(data)
        total_slots = sum(s["total_slots"] for s in data)
        total_occupied = sum(s["occupied_slots"] for s in data)
        avg_rate = (
            round(total_occupied / total_slots * 100, 1)
            if total_slots else 0
        )

        # Aggregate platform-wide history in last 48 hours
        from datetime import timedelta
        since_48h = timezone.now() - timedelta(hours=48)
        histories = OccupancyHistory.objects.filter(
            parking_lot__is_active=True,
            parking_lot__is_verified=True,
            recorded_at__gte=since_48h
        ).order_by("recorded_at")

        from collections import defaultdict
        hour_buckets = defaultdict(list)
        for h in histories:
            dt_hour = h.recorded_at.replace(minute=0, second=0, microsecond=0)
            hour_buckets[dt_hour].append(h.occupancy_rate)

        platform_history = []
        for dt_hour, rates in sorted(hour_buckets.items()):
            platform_history.append({
                "recorded_at": dt_hour.isoformat(),
                "occupancy_rate": round(sum(rates) / len(rates), 1)
            })

        return Response({
            "summary": {
                "total_lots": total_lots,
                "total_slots": total_slots,
                "total_occupied": total_occupied,
                "total_available": total_slots - total_occupied,
                "platform_occupancy_rate": avg_rate,
            },
            "lots": data,
            "history": platform_history,
        })
