from celery import Celery
from celery.schedules import crontab

app = Celery("smartpark")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# ── Periodic Task Schedule ────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Run occupancy detection every 2 minutes
    "occupancy-detection": {
        "task": "apps.payments.tasks.run_all_occupancy_detection",
        "schedule": crontab(minute="*/2"),
    },
    # Refresh demand forecasts every hour
    "refresh-forecasts": {
        "task": "apps.payments.tasks.refresh_all_forecasts",
        "schedule": crontab(minute=0),
    },
    # Fraud sweep every night at 2 AM
    "fraud-sweep": {
        "task": "apps.payments.tasks.run_fraud_sweep",
        "schedule": crontab(hour=2, minute=0),
    },
}
