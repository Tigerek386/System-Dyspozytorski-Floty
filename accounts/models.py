from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """Custom user with a role: dispatcher, fleet manager or driver."""

    class Role(models.TextChoices):
        DISPATCHER = "dispatcher", "Dispatcher"
        FLEET_MANAGER = "fleet_manager", "Fleet manager"
        DRIVER = "driver", "Driver"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DISPATCHER,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_driver(self):
        return self.role == self.Role.DRIVER

    def home_url(self):
        """Landing page for this role: drivers get their task overview."""
        if self.is_driver:
            return reverse("driver_dashboard")
        return reverse("dashboard")
