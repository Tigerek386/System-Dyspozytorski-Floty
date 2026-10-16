from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from .models import Driver, TransportOrder, Vehicle

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def logged_in_client(client):
    user = User.objects.create_user(username="dispatcher1", password="S3curePass!xyz")
    client.force_login(user)
    return client


@pytest.fixture
def vehicle():
    return Vehicle.objects.create(
        plate_number="W123ABC",
        max_load_capacity_kg=1000,
        technical_inspection_expiry="2027-01-01",
        insurance_expiry="2027-01-01",
    )


@pytest.fixture
def driver():
    return Driver.objects.create(first_name="Jan", last_name="Kowalski")


def order_data(vehicle, driver, start=None, weight=500):
    start = start or timezone.now().replace(microsecond=0) + timedelta(days=1)
    return {
        "customer": "Acme",
        "description": "pallets",
        "cargo_weight_kg": weight,
        "planned_start": start.strftime("%Y-%m-%dT%H:%M"),
        "planned_end": (start + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M"),
        "vehicle": vehicle.pk,
        "driver": driver.pk,
        "price_pln": "1000.00",
        "estimated_cost_pln": "300.00",
    }


# --- views: adding data from the dashboard page ---------------------------

def test_add_vehicle_via_dashboard(logged_in_client):
    resp = logged_in_client.post(
        reverse("dashboard"),
        {
            "form": "vehicle",
            "plate_number": "K456DEF",
            "vehicle_type": "van",
            "max_load_capacity_kg": 900,
            "technical_inspection_expiry": "2027-01-01",
            "insurance_expiry": "2027-01-01",
        },
    )

    assert resp.status_code == 302
    assert Vehicle.objects.filter(plate_number="K456DEF").exists()


def test_add_driver_via_dashboard(logged_in_client):
    resp = logged_in_client.post(
        reverse("dashboard"),
        {
            "form": "driver",
            "first_name": "Anna",
            "last_name": "Nowak",
            "license_category": "B",
            "phone": "+48 600 000 002",
            "is_active": "on",
        },
    )

    assert resp.status_code == 302
    assert Driver.objects.filter(last_name="Nowak").exists()


def test_add_order_via_dashboard(logged_in_client, vehicle, driver):
    data = order_data(vehicle, driver)
    data["form"] = "order"

    resp = logged_in_client.post(reverse("dashboard"), data)

    assert resp.status_code == 302
    order = TransportOrder.objects.get()
    assert order.customer == "Acme"
    assert order.status == TransportOrder.Status.NEW


def test_overweight_order_rejected(logged_in_client, vehicle, driver):
    data = order_data(vehicle, driver, weight=1500)  # capacity is 1000 kg
    data["form"] = "order"

    resp = logged_in_client.post(reverse("dashboard"), data)

    assert TransportOrder.objects.count() == 0
    assert b"exceeds the max load capacity of the vehicle" in resp.content


def test_time_conflict_for_vehicle_rejected(logged_in_client, vehicle, driver):
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    TransportOrder.objects.create(
        customer="Existing",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=driver,
    )

    data = order_data(vehicle, driver, start=start + timedelta(hours=1))  # overlaps
    data["form"] = "order"
    resp = logged_in_client.post(reverse("dashboard"), data)

    assert TransportOrder.objects.count() == 1
    assert b"overlaps with these times" in resp.content


def test_non_overlapping_order_allowed(logged_in_client, vehicle, driver):
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    TransportOrder.objects.create(
        customer="Existing",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=driver,
    )

    data = order_data(vehicle, driver, start=start + timedelta(hours=3))  # after the first one
    data["form"] = "order"
    resp = logged_in_client.post(reverse("dashboard"), data)

    assert TransportOrder.objects.count() == 2


def test_change_order_status_via_dashboard(logged_in_client, vehicle, driver):
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    order = TransportOrder.objects.create(
        customer="Acme",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=driver,
    )

    resp = logged_in_client.post(
        reverse("dashboard"),
        {"form": "status", "order_id": order.pk, "status": TransportOrder.Status.IN_PROGRESS},
    )

    assert resp.status_code == 302
    order.refresh_from_db()
    assert order.status == TransportOrder.Status.IN_PROGRESS


# --- model logic ------------------------------------------------------------

def test_profit_calculator(vehicle, driver):
    start = timezone.now()
    order = TransportOrder.objects.create(
        customer="Acme",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=driver,
        price_pln=1000.00,
        estimated_cost_pln=300.00,
    )

    assert order.profit_pln == 700.00


def test_completed_order_does_not_conflict(vehicle, driver):
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    TransportOrder.objects.create(
        customer="Old",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=driver,
        status=TransportOrder.Status.COMPLETED,
    )

    candidate = TransportOrder(
        vehicle=vehicle,
        driver=driver,
        planned_start=start,  # same time slot as the completed order
        planned_end=start + timedelta(hours=2),
    )
    assert not candidate.has_time_conflict()


def test_vehicle_protected_from_deletion_with_orders(vehicle, driver):
    from django.db.models import ProtectedError

    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    TransportOrder.objects.create(
        customer="Acme",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=driver,
    )

    with pytest.raises(ProtectedError):
        vehicle.delete()


# --- driver role: access control and task overview --------------------------

@pytest.fixture
def driver_user():
    """A driver-role user account."""
    return User.objects.create_user(
        username="driver1", password="S3curePass!xyz", role=User.Role.DRIVER
    )


@pytest.fixture
def driver_client(client, driver_user):
    """A client logged in as a driver-role user."""
    client.force_login(driver_user)
    return client


@pytest.fixture
def linked_driver(driver, driver_user):
    """A Driver profile linked to the driver-role user account."""
    driver.user = driver_user
    driver.save(update_fields=["user"])
    return driver


def test_driver_cannot_access_main_dashboard(driver_client):
    resp = driver_client.get(reverse("dashboard"))

    assert resp.status_code == 302
    assert resp.url == reverse("driver_dashboard")


def test_staff_cannot_access_driver_page(logged_in_client):
    resp = logged_in_client.get(reverse("driver_dashboard"))

    assert resp.status_code == 302
    assert resp.url == reverse("dashboard")


def test_unlinked_driver_sees_no_tasks(driver_client, vehicle, driver):
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    TransportOrder.objects.create(
        customer="Acme",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=driver,
    )

    resp = driver_client.get(reverse("driver_dashboard"))

    assert resp.status_code == 200
    assert b"No driver profile is linked" in resp.content
    assert b"Acme" not in resp.content


def test_driver_sees_only_own_orders(driver_client, vehicle, linked_driver):
    other = Driver.objects.create(first_name="Other", last_name="Driver")
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    mine = TransportOrder.objects.create(
        customer="MyCustomer",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=linked_driver,
    )
    TransportOrder.objects.create(
        customer="OtherCustomer",
        cargo_weight_kg=100,
        planned_start=start + timedelta(days=2),
        planned_end=start + timedelta(days=2) + timedelta(hours=2),
        vehicle=vehicle,
        driver=other,
    )

    resp = driver_client.get(reverse("driver_dashboard"))

    assert resp.status_code == 200
    assert b"MyCustomer" in resp.content
    assert b"OtherCustomer" not in resp.content


def test_driver_completed_order_moves_to_history(driver_client, vehicle, linked_driver):
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    order = TransportOrder.objects.create(
        customer="DoneDeal",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=linked_driver,
        status=TransportOrder.Status.COMPLETED,
    )

    resp = driver_client.get(reverse("driver_dashboard"))

    assert resp.status_code == 200
    assert b"DoneDeal" in resp.content


def test_link_driver_account_via_dashboard(logged_in_client, vehicle, linked_driver):
    # the profile is already linked; re-linking to the same account is fine
    resp = logged_in_client.post(
        reverse("dashboard"),
        {
            "form": "link_driver",
            "driver_id": linked_driver.pk,
            "user_id": linked_driver.user.pk,
        },
    )

    assert resp.status_code == 302
    linked_driver.refresh_from_db()
    assert linked_driver.user.username == "driver1"


def test_link_driver_account_rejects_already_linked_user(
    logged_in_client, vehicle, linked_driver
):
    other = Driver.objects.create(first_name="Other", last_name="Driver")

    resp = logged_in_client.post(
        reverse("dashboard"),
        {
            "form": "link_driver",
            "driver_id": other.pk,
            "user_id": linked_driver.user.pk,  # already taken
        },
    )

    assert resp.status_code == 302
    other.refresh_from_db()
    assert other.user is None


def test_driver_can_update_status_of_own_order(driver_client, vehicle, linked_driver):
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    order = TransportOrder.objects.create(
        customer="MyCustomer",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=linked_driver,
    )

    resp = driver_client.post(
        reverse("driver_dashboard"),
        {"order_id": order.pk, "status": TransportOrder.Status.COMPLETED},
    )

    assert resp.status_code == 302
    order.refresh_from_db()
    assert order.status == TransportOrder.Status.COMPLETED


def test_driver_cannot_update_status_of_other_order(driver_client, vehicle, driver):
    other_account = User.objects.create_user(
        username="other1", password="S3curePass!xyz", role=User.Role.DRIVER
    )
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    order = TransportOrder.objects.create(
        customer="OtherCustomer",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=driver,  # not linked to the logged-in driver
    )

    resp = driver_client.post(
        reverse("driver_dashboard"),
        {"order_id": order.pk, "status": TransportOrder.Status.COMPLETED},
    )

    assert resp.status_code == 404
    order.refresh_from_db()
    assert order.status != TransportOrder.Status.COMPLETED


def test_driver_cannot_set_forbidden_status(driver_client, vehicle, linked_driver):
    start = timezone.now().replace(microsecond=0) + timedelta(days=1)
    order = TransportOrder.objects.create(
        customer="MyCustomer",
        cargo_weight_kg=100,
        planned_start=start,
        planned_end=start + timedelta(hours=2),
        vehicle=vehicle,
        driver=linked_driver,
    )

    resp = driver_client.post(
        reverse("driver_dashboard"),
        {"order_id": order.pk, "status": TransportOrder.Status.CANCELLED},
    )

    assert resp.status_code == 302
    order.refresh_from_db()
    assert order.status != TransportOrder.Status.CANCELLED
