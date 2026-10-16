from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegistrationForm(UserCreationForm):
    """Registration form: username, email, role and password."""

    class Meta:
        model = User
        fields = ("username", "email", "role")
