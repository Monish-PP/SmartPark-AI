from django.urls import path
from apps.occupancy.views import (
    OccupancyUpdateView,
    OccupancyDetailView,
    OccupancyAllView,
)

urlpatterns = [
    # Edge service → Django (POST only)
    path("update/", OccupancyUpdateView.as_view(), name="occupancy-update"),

    # Frontend reads
    path("all/", OccupancyAllView.as_view(), name="occupancy-all"),
    path("<str:parking_id>/", OccupancyDetailView.as_view(), name="occupancy-detail"),
]
