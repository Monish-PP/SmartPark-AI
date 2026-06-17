import environ
import os
from pathlib import Path
from datetime import timedelta

env = environ.Env(DEBUG=(bool, False))
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    "channels",
    "drf_yasg",
    # SmartPark apps
    "apps.users",
    "apps.parking",
    "apps.bookings",
    "apps.payments",
    "apps.analytics",
    "apps.notifications",
    "apps.occupancy",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "smartpark.urls"
WSGI_APPLICATION = "smartpark.wsgi.application"
ASGI_APPLICATION = "smartpark.asgi.application"

# ── Database (MongoDB via django-mongodb-backend) ─────────────────────────
MONGO_URI = env("MONGO_URI", default="mongodb://localhost:27017")
MONGO_AUTH_MECHANISM = env("MONGO_AUTH_MECHANISM", default="")

DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "NAME": env("MONGO_DB_NAME", default="smartpark"),
        "CLIENT": {
            "host": MONGO_URI,
            "uuidRepresentation": "standard",
        },
    }
}

if MONGO_AUTH_MECHANISM:
    DATABASES["default"]["OPTIONS"] = {"authMechanism": MONGO_AUTH_MECHANISM}

# ── Custom User Model ────────────────────────────────────────────────────────
AUTH_USER_MODEL = "users.User"

# ── REST Framework ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ── JWT ──────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# ── CORS ─────────────────────────────────────────────────────────────────────
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
CORS_ALLOWED_ORIGINS = env.list("CORS_ORIGINS", default=DEFAULT_CORS_ORIGINS)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG

# ── Redis / Channels ─────────────────────────────────────────────────────────
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

# ── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

# ── Razorpay ─────────────────────────────────────────────────────────────────
RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET")

# ── Firebase ─────────────────────────────────────────────────────────────────
FIREBASE_CREDENTIALS_PATH = env("FIREBASE_CREDENTIALS_PATH", default="firebase-credentials.json")

# ── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL = env("SUPABASE_URL")
SUPABASE_KEY = env("SUPABASE_KEY")

# ── Edge AI Service ───────────────────────────────────────────────────────────
# Shared secret between occupancy-service and Django backend (X-Edge-Secret header)
EDGE_AI_SECRET = env("EDGE_AI_SECRET", default="changeme-edge-secret")

# ── Google Maps ──────────────────────────────────────────────────────────────
GOOGLE_MAPS_API_KEY = env("GOOGLE_MAPS_API_KEY")

# ── ML Model Paths ───────────────────────────────────────────────────────────
ML_MODELS_DIR = BASE_DIR / "ml_models"
YOLO_MODEL_PATH = ML_MODELS_DIR / "yolov8_parking.pt"
RECOMMENDER_MODEL_PATH = ML_MODELS_DIR / "recommender.pkl"
FORECASTER_MODEL_PATH = ML_MODELS_DIR / "forecaster.pkl"
FRAUD_MODEL_PATH = ML_MODELS_DIR / "fraud_detector.pkl"

# ── Static / Media ───────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
