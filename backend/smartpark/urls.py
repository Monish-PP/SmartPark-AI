from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="SmartPark AI API",
        default_version="v1",
        description="AI-powered Smart Parking Marketplace API",
        contact=openapi.Contact(email="admin@smartpark.ai"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", RedirectView.as_view(url="swagger/", permanent=False), name="home"),
    path("admin/", admin.site.urls),

    # API routes
    path("api/auth/", include("apps.users.urls")),
    path("api/parking/", include("apps.parking.urls")),
    path("api/bookings/", include("apps.bookings.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/occupancy/", include("apps.occupancy.urls")),

    # Swagger docs
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
]
