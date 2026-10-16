from django.contrib import admin

from .models import Driver, TransportOrder, Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "plate_number",
        "vehicle_type",
        "max_load_capacity_kg",
        "technical_inspection_expiry",
        "insurance_expiry",
    )


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "license_category", "phone", "is_active")


@admin.register(TransportOrder)
class TransportOrderAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "customer",
        "vehicle",
        "driver",
        "planned_start",
        "planned_end",
        "status",
        "profit_pln",
    )
    list_filter = ("status",)
