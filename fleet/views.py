from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User

from .forms import DriverForm, TransportOrderForm, VehicleForm
from .models import Driver, TransportOrder, Vehicle


def _staff_only(view):
    """Redirect driver-role users to their task overview."""
    def wrapper(request, *args, **kwargs):
        if request.user.is_driver:
            return redirect("driver_dashboard")
        return view(request, *args, **kwargs)
    return wrapper


@login_required
@_staff_only
def dashboard(request):
    """Single page for dispatchers and fleet managers: view and add vehicles,
    drivers and transport orders, link driver accounts, and change an
    order's status (lifecycle)."""
    context = {
        "vehicles": Vehicle.objects.all(),
        "drivers": Driver.objects.select_related("user").all(),
        "orders": TransportOrder.objects.select_related("vehicle", "driver").all(),
        "order_statuses": TransportOrder.Status.choices,
        "driver_accounts": User.objects.filter(role=User.Role.DRIVER).order_by("username"),
        "vehicle_form": VehicleForm(),
        "driver_form": DriverForm(),
        "order_form": TransportOrderForm(),
    }

    if request.method == "POST":
        form_key = request.POST.get("form")

        if form_key in ("vehicle", "driver", "order"):
            form_class = {
                "vehicle": VehicleForm,
                "driver": DriverForm,
                "order": TransportOrderForm,
            }[form_key]
            form = form_class(request.POST)
            if form.is_valid():
                obj = form.save()
                messages.success(request, f"Saved: {obj}")
                return redirect("dashboard")
            context[f"{form_key}_form"] = form  # re-render with validation errors
        elif form_key == "link_driver":
            driver = get_object_or_404(Driver, pk=request.POST.get("driver_id"))
            account = get_object_or_404(
                User, pk=request.POST.get("user_id"), role=User.Role.DRIVER
            )
            if Driver.objects.filter(user=account).exclude(pk=driver.pk).exists():
                messages.error(
                    request,
                    f"Account {account.username} is already linked to "
                    f"{driver}.",
                )
            else:
                driver.user = account
                driver.save(update_fields=["user"])
                messages.success(
                    request,
                    f"Linked account {account.username} to {driver}.",
                )
            return redirect("dashboard")
        elif form_key == "status":
            order = get_object_or_404(TransportOrder, pk=request.POST.get("order_id"))
            new_status = request.POST.get("status")
            if new_status in TransportOrder.Status.values:
                order.status = new_status
                order.save(update_fields=["status"])
                messages.success(
                    request,
                    f"Order #{order.pk} status changed to {order.get_status_display()}.",
                )
            return redirect("dashboard")

    return render(request, "fleet/dashboard.html", context)


#: statuses a driver may move their own order to from the task overview
DRIVER_ALLOWED_STATUSES = (TransportOrder.Status.IN_PROGRESS, TransportOrder.Status.COMPLETED)


@login_required
def driver_dashboard(request):
    """Task overview for logged-in drivers: only orders assigned to the
    driver profile linked to their account."""
    if not request.user.is_driver:
        return redirect("dashboard")

    profile = getattr(request.user, "driver_profile", None)
    orders = (
        TransportOrder.objects.select_related("vehicle")
        .filter(driver=profile)
    ) if profile else TransportOrder.objects.none()

    context = {
        "profile": profile,
        "active_orders": [o for o in orders if o.is_active],
        "history": [o for o in orders if not o.is_active],
        "driver_statuses": [s for s in TransportOrder.Status.choices
                            if s[0] in DRIVER_ALLOWED_STATUSES],
    }

    if request.method == "POST":
        # an unlinked driver has an empty queryset, so any order id 404s
        order = get_object_or_404(orders, pk=request.POST.get("order_id"))
        new_status = request.POST.get("status")
        if new_status in DRIVER_ALLOWED_STATUSES:
            order.status = new_status
            order.save(update_fields=["status"])
            messages.success(
                request,
                f"Order #{order.pk} status changed to {order.get_status_display()}.",
            )
        return redirect("driver_dashboard")

    return render(request, "fleet/driver_dashboard.html", context)
