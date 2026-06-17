from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.conf import settings
import razorpay

from apps.bookings.models import Booking, BookingReview
from apps.bookings.serializers import (
    BookingCreateSerializer, BookingSerializer, BookingReviewSerializer,
)
from apps.payments.tasks import process_refund


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        # Create Razorpay order
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        rp_order = client.order.create(
            {
                "amount": int(float(booking.estimated_amount) * 100),  # paise
                "currency": "INR",
                "receipt": str(booking.id),
                "payment_capture": 1,
            }
        )
        booking.razorpay_order_id = rp_order["id"]
        booking.save()

        return Response(
            {
                "booking": BookingSerializer(booking).data,
                "razorpay_order_id": rp_order["id"],
                "amount": rp_order["amount"],
                "currency": "INR",
                "key": settings.RAZORPAY_KEY_ID,
            },
            status=status.HTTP_201_CREATED,
        )


class BookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by("-created_at")


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)


class BookingEntryView(APIView):
    """Mark actual vehicle entry — starts live billing."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        booking = Booking.objects.get(pk=pk, user=request.user)
        if booking.status != "confirmed":
            return Response({"detail": "Booking must be confirmed."}, status=400)
        booking.actual_entry = timezone.now()
        booking.status = "active"
        booking.slot.is_occupied = True
        booking.slot.save()
        booking.save()
        return Response(BookingSerializer(booking).data)


class BookingExitView(APIView):
    """Mark vehicle exit — finalises billing and triggers refund if applicable."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        booking = Booking.objects.get(pk=pk, user=request.user)
        if booking.status != "active":
            return Response({"detail": "Booking is not active."}, status=400)

        booking.actual_exit = timezone.now()
        booking.status = "completed"
        booking.calculate_final_amount()
        booking.calculate_refund()
        booking.slot.is_occupied = False
        booking.slot.save()
        booking.save()

        # Trigger async refund if applicable
        if booking.refund_amount > 0:
            process_refund.delay(str(booking.id))

        return Response(BookingSerializer(booking).data)


class BookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        booking = Booking.objects.get(pk=pk, user=request.user)
        if booking.status not in ["pending", "confirmed"]:
            return Response({"detail": "Cannot cancel at this stage."}, status=400)
        booking.status = "cancelled"
        booking.slot.is_available = True
        booking.slot.save()
        booking.save()
        return Response({"detail": "Booking cancelled."})


class PaymentVerifyView(APIView):
    """Razorpay webhook / payment verification."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": request.data["razorpay_order_id"],
                    "razorpay_payment_id": request.data["razorpay_payment_id"],
                    "razorpay_signature": request.data["razorpay_signature"],
                }
            )
        except Exception:
            return Response({"detail": "Invalid signature."}, status=400)

        booking = Booking.objects.get(
            razorpay_order_id=request.data["razorpay_order_id"]
        )
        booking.razorpay_payment_id = request.data["razorpay_payment_id"]
        booking.is_paid = True
        booking.status = "confirmed"
        booking.save()
        return Response({"detail": "Payment verified."})


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = BookingReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
