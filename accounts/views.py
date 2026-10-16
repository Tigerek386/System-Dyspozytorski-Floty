from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import UserRegistrationForm


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        # Drivers land on their task overview, staff on the dashboard.
        if self.request.user.is_authenticated:
            return self.request.user.home_url()
        return super().get_success_url()


def register(request):
    """Create a new user (dispatcher, fleet manager or driver) and log them in."""
    if request.user.is_authenticated:
        return redirect(request.user.home_url())

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome, {user.username}! You are registered as a "
                f"{user.get_role_display().lower()}.",
            )
            return redirect(user.home_url())
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})
