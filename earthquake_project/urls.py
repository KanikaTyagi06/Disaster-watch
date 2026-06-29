"""
earthquake_project/urls.py  –  Root URL configuration.

Web routes   → earthquake_app.urls
REST API     → earthquake_app.api_urls
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # ── HTML web interface ────────────────────────────────────────────────
    path("", include("earthquake_app.urls")),

    # ── REST API (JSON) ───────────────────────────────────────────────────
    # GET  /api/earthquakes/          → list all earthquakes
    # GET  /api/earthquakes/<id>/     → single earthquake
    # POST /api/fetch/                → trigger USGS fetch
    # GET  /api/dashboard/stats/      → dashboard stats
    # GET  /api/users/                → list users
    path("api/", include("earthquake_app.api_urls")),
]
