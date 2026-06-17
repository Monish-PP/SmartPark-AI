from django.urls import path
from apps.parking.views import (
    ParkingLotListCreateView, ParkingLotDetailView,
    ParkingSearchView, SlotListCreateView, OccupancyStatusView,
)

urlpatterns = [
    # Parking lots
    path("", ParkingLotListCreateView.as_view(), name="lot-list"),
    path("<uuid:pk>/", ParkingLotDetailView.as_view(), name="lot-detail"),

    # AI search
    path("search/", ParkingSearchView.as_view(), name="parking-search"),

    # Slots
    path("<uuid:lot_pk>/slots/", SlotListCreateView.as_view(), name="slot-list"),

    # Live occupancy
    path("<uuid:lot_pk>/occupancy/", OccupancyStatusView.as_view(), name="occupancy"),
]
