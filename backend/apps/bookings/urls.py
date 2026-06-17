from django.urls import path
from apps.bookings.views import (
    BookingCreateView, BookingListView, BookingDetailView,
    BookingEntryView, BookingExitView, BookingCancelView,
    PaymentVerifyView, ReviewCreateView,
)

urlpatterns = [
    path("", BookingListView.as_view(), name="booking-list"),
    path("create/", BookingCreateView.as_view(), name="booking-create"),
    path("<uuid:pk>/", BookingDetailView.as_view(), name="booking-detail"),
    path("<uuid:pk>/entry/", BookingEntryView.as_view(), name="booking-entry"),
    path("<uuid:pk>/exit/", BookingExitView.as_view(), name="booking-exit"),
    path("<uuid:pk>/cancel/", BookingCancelView.as_view(), name="booking-cancel"),
    path("verify-payment/", PaymentVerifyView.as_view(), name="verify-payment"),
    path("reviews/", ReviewCreateView.as_view(), name="review-create"),
]
