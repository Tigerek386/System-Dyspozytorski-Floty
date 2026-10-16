from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("driver/", views.driver_dashboard, name="driver_dashboard"),
]
