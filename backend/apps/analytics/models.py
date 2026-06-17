from django.db import models
from apps.users.models import User
import uuid


class FraudEvent(models.Model):
    """Admin-visible fraud detection events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fraud_events")
    anomaly_score = models.FloatField()
    features = models.JSONField(default=dict)
    is_reviewed = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"FraudEvent {self.user.email} — {self.anomaly_score:.3f}"
