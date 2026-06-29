"""
earthquake_app/api_urls.py  –  REST API (JSON) URL routes.
Mounted under /api/ by the project urls.py.
"""
from django.urls import path
from .api_views import (
    EarthquakeListAPIView,
    EarthquakeDetailAPIView,
    FetchEarthquakesAPIView,
    DashboardStatsAPIView,
    UserListAPIView,
)

urlpatterns = [
    # GET  /api/earthquakes/
    path("earthquakes/",          EarthquakeListAPIView.as_view(),   name="api-earthquake-list"),

    # GET  /api/earthquakes/<id>/
    path("earthquakes/<str:earthquake_id>/", EarthquakeDetailAPIView.as_view(), name="api-earthquake-detail"),

    # POST /api/fetch/
    path("fetch/",                FetchEarthquakesAPIView.as_view(), name="api-fetch"),

    # GET  /api/dashboard/stats/
    path("dashboard/stats/",      DashboardStatsAPIView.as_view(),   name="api-dashboard-stats"),

    # GET  /api/users/
    path("users/",                UserListAPIView.as_view(),          name="api-users"),
]
