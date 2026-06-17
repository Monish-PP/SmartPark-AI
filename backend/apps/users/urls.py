from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views import (
    RegisterView, LoginView, ProfileView,
    VehicleListCreateView, VehicleDetailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("vehicles/", VehicleListCreateView.as_view(), name="vehicles"),
    path("vehicles/<uuid:pk>/", VehicleDetailView.as_view(), name="vehicle-detail"),
]
