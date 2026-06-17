from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    USER = "user"
    OWNER = "owner"
    ADMIN = "admin"
    ROLE_CHOICES = [(USER, "User"), (OWNER, "Owner"), (ADMIN, "Admin")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=USER)
    profile_image = models.URLField(blank=True)
    fcm_token = models.TextField(blank=True)         # Firebase Cloud Messaging

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"


class Vehicle(models.Model):
    TWO_WHEELER = "two_wheeler"
    FOUR_WHEELER = "four_wheeler"
    HEAVY = "heavy"
    VEHICLE_TYPES = [
        (TWO_WHEELER, "Two Wheeler"),
        (FOUR_WHEELER, "Four Wheeler"),
        (HEAVY, "Heavy Vehicle"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vehicles")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    number_plate = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50, blank=True)
    model_name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.number_plate} ({self.vehicle_type})"
