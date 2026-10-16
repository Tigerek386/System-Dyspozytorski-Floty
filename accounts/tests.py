import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db

User = get_user_model()

REGISTER_DATA = {
    "username": "dispatcher1",
    "email": "disp@example.com",
    "role": User.Role.DISPATCHER,
    "password1": "S3curePass!xyz",
    "password2": "S3curePass!xyz",
}


@pytest.fixture
def logged_in_client(client):
    """A client with an authenticated dispatcher."""
    user = User.objects.create_user(
        username="dispatcher1", password="S3curePass!xyz", role=User.Role.DISPATCHER
    )
    client.force_login(user)
    return client


def test_register_creates_user_with_dispatcher_role(client):
    resp = client.post(reverse("register"), REGISTER_DATA)

    user = User.objects.get(username="dispatcher1")
    assert user.role == User.Role.DISPATCHER
    assert user.check_password("S3curePass!xyz")
    assert resp.status_code == 302
    assert resp.url == reverse("dashboard")


def test_register_with_fleet_manager_role(client):
    data = {**REGISTER_DATA, "username": "manager1", "role": User.Role.FLEET_MANAGER}
    client.post(reverse("register"), data)

    user = User.objects.get(username="manager1")
    assert user.role == User.Role.FLEET_MANAGER


def test_register_with_driver_role(client):
    data = {**REGISTER_DATA, "username": "driver1", "role": User.Role.DRIVER}
    resp = client.post(reverse("register"), data)

    user = User.objects.get(username="driver1")
    assert user.role == User.Role.DRIVER
    assert user.is_driver
    # drivers land on their task overview, not the dashboard
    assert resp.status_code == 302
    assert resp.url == reverse("driver_dashboard")


def test_login_with_driver_role_redirects_to_task_overview(client):
    User.objects.create_user(username="driver1", password="S3curePass!xyz", role=User.Role.DRIVER)

    resp = client.post(
        reverse("login"), {"username": "driver1", "password": "S3curePass!xyz"}
    )

    assert resp.status_code == 302
    assert resp.url == reverse("driver_dashboard")


def test_register_with_invalid_password_rejected(client):
    data = {**REGISTER_DATA, "password1": "short", "password2": "short"}
    resp = client.post(reverse("register"), data)

    assert not User.objects.filter(username="dispatcher1").exists()
    assert resp.status_code == 200


def test_login_logs_user_in(client):
    User.objects.create_user(
        username="fleetmanager1", password="S3curePass!xyz", role=User.Role.FLEET_MANAGER
    )

    resp = client.post(
        reverse("login"), {"username": "fleetmanager1", "password": "S3curePass!xyz"}
    )

    assert resp.status_code == 302
    assert resp.url == reverse("dashboard")


def test_login_with_wrong_password_fails(client):
    User.objects.create_user(username="dispatcher1", password="S3curePass!xyz")

    resp = client.post(
        reverse("login"), {"username": "dispatcher1", "password": "wrong-password"}
    )

    assert resp.status_code == 200


def test_logout(client, logged_in_client):
    resp = logged_in_client.post(reverse("logout"))

    assert resp.status_code == 302
    assert not logged_in_client.session.get("_auth_user_id")


def test_dashboard_requires_login(client):
    resp = client.get(reverse("dashboard"))

    assert resp.status_code == 302
    assert reverse("login") in resp.url


def test_dashboard_visible_to_logged_in_user(logged_in_client):
    resp = logged_in_client.get(reverse("dashboard"))

    assert resp.status_code == 200
    assert b"Dashboard" in resp.content
