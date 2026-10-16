from django.conf import settings
from django.db import models


class Vehicle(models.Model):
    """A vehicle in the fleet.

    Tracks the max load capacity (used to validate cargo weight) and the
    technical inspection / insurance expiry dates.
    """

    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=50, default="truck")
    max_load_capacity_kg = models.PositiveIntegerField()
    technical_inspection_expiry = models.DateField()
    insurance_expiry = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["plate_number"]

    def __str__(self):
        return self.plate_number


class Driver(models.Model):
    """A driver that can be assigned to transport orders.

    Can optionally be linked to a registered driver account (a User with
    the DRIVER role) by a dispatcher or fleet manager, so the driver can
    log in and see their own tasks.
    """

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    license_category = models.CharField(max_length=5, default="C")
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="driver_profile",
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TransportOrder(models.Model):
    """A registered transport order (zlecenie).

    Has planned start/end times, an assigned vehicle and driver, a status
    that follows the order lifecycle, and revenue/cost fields used by the
    profitability calculator.
    """

    class Status(models.TextChoices):
        NEW = "new", "New"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    #: statuses that occupy the vehicle/driver and can conflict in time
    ACTIVE_STATUSES = [Status.NEW, Status.ASSIGNED, Status.IN_PROGRESS]

    customer = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cargo_weight_kg = models.PositiveIntegerField()
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="orders")
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    price_pln = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_cost_pln = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["planned_start"]

    def __str__(self):
        return f"#{self.pk} {self.customer} ({self.status})"

    @property
    def profit_pln(self):
        """Profitability calculator: revenue minus estimated cost."""
        return self.price_pln - self.estimated_cost_pln

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    def has_time_conflict(self):
        """Return True if this order overlaps in time with an active order
        of the same vehicle or the same driver."""
        if not (self.planned_start and self.planned_end):
            return False
        for related_name in ("vehicle", "driver"):
            conflict = TransportOrder.objects.filter(
                **{related_name: getattr(self, related_name)},
                status__in=self.ACTIVE_STATUSES,
                planned_start__lt=self.planned_end,
                planned_end__gt=self.planned_start,
            ).exclude(pk=self.pk)
            if conflict.exists():
                return True
        return False
