"""Populate the database with sample data so the app can be tested right away.

Run:  uv run python manage.py seed
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from fleet.models import Driver, TransportOrder, Vehicle


class Command(BaseCommand):
    help = "Seed the database with demo users, vehicles, drivers and orders."

    def handle(self, *args, **options):
        User = get_user_model()

        dispatcher, _ = User.objects.get_or_create(
            username="dispatcher1",
            defaults={"email": "dispatcher1@example.com", "role": User.Role.DISPATCHER},
        )
        dispatcher.set_password("password123")
        dispatcher.save()

        manager, _ = User.objects.get_or_create(
            username="fleetmanager1",
            defaults={"email": "manager1@example.com", "role": User.Role.FLEET_MANAGER},
        )
        manager.set_password("password123")
        manager.save()

        driver_account, _ = User.objects.get_or_create(
            username="driver1",
            defaults={"email": "driver1@example.com", "role": User.Role.DRIVER},
        )
        driver_account.set_password("password123")
        driver_account.save()

        if Vehicle.objects.exists():
            # make sure the demo driver account is linked (previously seeded DBs)
            unlinked = Driver.objects.filter(user__isnull=True).first()
            if unlinked is not None:
                unlinked.user = driver_account
                unlinked.save(update_fields=["user"])
            self.stdout.write(self.style.WARNING("Data already present, skipping seed."))
            return

        vehicle_a = Vehicle.objects.create(
            plate_number="W123ABC",
            vehicle_type="truck",
            max_load_capacity_kg=12000,
            technical_inspection_expiry="2027-06-01",
            insurance_expiry="2026-12-31",
        )
        vehicle_b = Vehicle.objects.create(
            plate_number="K456DEF",
            vehicle_type="van",
            max_load_capacity_kg=900,
            technical_inspection_expiry="2027-03-15",
            insurance_expiry="2026-11-30",
        )

        driver_a = Driver.objects.create(
            first_name="Jan", last_name="Kowalski", license_category="C", phone="+48 600 000 001"
        )
        driver_b = Driver.objects.create(
            first_name="Anna", last_name="Nowak", license_category="B", phone="+48 600 000 002"
        )

        # link the demo driver account to Jan Kowalski so it can log in right away
        if driver_a.user is None:
            driver_a.user = driver_account
            driver_a.save(update_fields=["user"])

        base = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)

        TransportOrder.objects.create(
            customer="Acme Sp. z o.o.",
            description="Pallets of electronics, Gdansk -> Wroclaw",
            cargo_weight_kg=8500,
            planned_start=base,
            planned_end=base + timedelta(hours=10),
            vehicle=vehicle_a,
            driver=driver_a,
            status=TransportOrder.Status.ASSIGNED,
            price_pln=2400.00,
            estimated_cost_pln=900.00,
        )
        TransportOrder.objects.create(
            customer="Biedronka",
            description="Grocery delivery, Warsaw -> Krakow",
            cargo_weight_kg=750,
            planned_start=base + timedelta(hours=12),
            planned_end=base + timedelta(hours=16),
            vehicle=vehicle_b,
            driver=driver_b,
            status=TransportOrder.Status.NEW,
            price_pln=450.00,
            estimated_cost_pln=200.00,
        )
        TransportOrder.objects.create(
            customer="Cargobit",
            description="Furniture, Poznan -> Gdansk",
            cargo_weight_kg=3000,
            planned_start=base - timedelta(days=7),
            planned_end=base - timedelta(days=6),
            vehicle=vehicle_a,
            driver=driver_a,
            status=TransportOrder.Status.COMPLETED,
            price_pln=1800.00,
            estimated_cost_pln=950.00,
        )

        self.stdout.write(self.style.SUCCESS(
            "Seeded 2 users (dispatcher1 / fleetmanager1, password: password123), "
            "2 vehicles, 2 drivers and 3 orders."
        ))
