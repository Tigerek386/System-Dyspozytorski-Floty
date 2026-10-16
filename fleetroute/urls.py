"""
URL configuration for the FleetRoute project.
"""
from django.http import JsonResponse
from django.urls import path
from django.contrib import admin
from django.urls import include, path

def health(_request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("health", health),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("fleet.urls")),
]
