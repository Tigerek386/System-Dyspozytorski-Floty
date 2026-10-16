from django import forms

from .models import Driver, TransportOrder, Vehicle


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "plate_number",
            "vehicle_type",
            "max_load_capacity_kg",
            "technical_inspection_expiry",
            "insurance_expiry",
            "notes",
        ]


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ["first_name", "last_name", "license_category", "phone", "is_active"]


class TransportOrderForm(forms.ModelForm):
    """Order form with the two validations from the MVP spec:

    * cargo weight must not exceed the vehicle's max load capacity
    * the vehicle/driver must not have an overlapping active order
    """

    class Meta:
        model = TransportOrder
        fields = [
            "customer",
            "description",
            "cargo_weight_kg",
            "planned_start",
            "planned_end",
            "vehicle",
            "driver",
            "price_pln",
            "estimated_cost_pln",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("planned_start", "planned_end"):
            self.fields[field_name].widget = forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            )
            self.fields[field_name].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned_data = super().clean()

        vehicle = cleaned_data.get("vehicle")
        weight = cleaned_data.get("cargo_weight_kg")
        start = cleaned_data.get("planned_start")
        end = cleaned_data.get("planned_end")

        if vehicle and weight is not None and weight > vehicle.max_load_capacity_kg:
            self.add_error(
                "cargo_weight_kg",
                f"Cargo weight ({weight} kg) exceeds the max load capacity "
                f"of the vehicle ({vehicle.max_load_capacity_kg} kg).",
            )

        if start and end and start >= end:
            self.add_error("planned_end", "End time must be after the start time.")

        if (
            vehicle
            and cleaned_data.get("driver")
            and start
            and end
            and start < end
        ):
            candidate = TransportOrder(
                vehicle=vehicle,
                driver=cleaned_data["driver"],
                planned_start=start,
                planned_end=end,
            )
            if candidate.has_time_conflict():
                self.add_error(
                    "planned_start",
                    "The selected vehicle or driver already has an active "
                    "order that overlaps with these times.",
                )

        return cleaned_data
