"""earthquake_app/admin.py  –  Django admin registrations."""
from django.contrib import admin
from .models import Earthquake, AppUser


@admin.register(Earthquake)
class EarthquakeAdmin(admin.ModelAdmin):
    list_display  = ("earthquake_id", "magnitude", "place", "time", "depth")
    list_filter   = ("magnitude",)
    search_fields = ("place", "earthquake_id")
    ordering      = ("-time",)
    list_per_page = 50


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display  = ("user_id", "username", "email", "created_at")
    search_fields = ("username", "email")
    ordering      = ("-created_at",)
    # Never show password field in admin
    exclude       = ("password",)
