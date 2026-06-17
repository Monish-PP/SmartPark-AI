from django.urls import path
from apps.analytics.views import (
    OwnerDashboardView, AdminAnalyticsView,
    HeatmapDataView, ForecastView,
)

urlpatterns = [
    path("owner/",              OwnerDashboardView.as_view(),  name="owner-dashboard"),
    path("admin/",              AdminAnalyticsView.as_view(),  name="admin-analytics"),
    path("heatmap/",            HeatmapDataView.as_view(),     name="heatmap"),
    path("forecast/<uuid:lot_pk>/", ForecastView.as_view(),    name="forecast"),
]
