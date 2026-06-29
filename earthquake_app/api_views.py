"""
earthquake_app/api_views.py
============================
REST API views — all return JSON.

Endpoints:
  GET  /api/earthquakes/            List all earthquakes (paginated, filterable)
  GET  /api/earthquakes/<id>/       Single earthquake detail
  POST /api/fetch/                  Trigger USGS fetch
  GET  /api/dashboard/stats/        Dashboard statistics
  GET  /api/users/                  List users (no passwords)

Authentication: session-based (same session cookie as the web UI).
For a pure API client, check the Authorization header in middleware.
"""
from rest_framework.views     import APIView
from rest_framework.response  import Response
from rest_framework           import status
from rest_framework.pagination import PageNumberPagination

from django.db.models import Max, Q

from .models      import Earthquake, AppUser
from .serializers import (
    EarthquakeSerializer,
    EarthquakeCreateSerializer,
    AppUserSerializer,
    DashboardStatsSerializer,
)
from .usgs_fetcher import fetch_and_store


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM PAGINATION
# ─────────────────────────────────────────────────────────────────────────────
class EarthquakePagination(PageNumberPagination):
    page_size             = 20
    page_size_query_param = "page_size"
    max_page_size         = 100


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/earthquakes/
# ─────────────────────────────────────────────────────────────────────────────
class EarthquakeListAPIView(APIView):
    """
    GET /api/earthquakes/

    Query parameters:
        search    — keyword in place or earthquake_id
        mag_min   — minimum magnitude  (float)
        mag_max   — maximum magnitude  (float)
        date_from — YYYY-MM-DD
        date_to   — YYYY-MM-DD
        sort      — field name, prefix with - for DESC  (default: -time)
        page      — page number (default 1)
        page_size — records per page (default 20, max 100)

    Response 200:
        {
          "count":    <total matching records>,
          "next":     <url or null>,
          "previous": <url or null>,
          "results":  [ { earthquake fields ... }, ... ]
        }
    """

    def get(self, request):
        qs = Earthquake.objects.all()

        # ── Filters ───────────────────────────────────────────────────────
        search    = request.query_params.get("search", "").strip()
        mag_min   = request.query_params.get("mag_min")
        mag_max   = request.query_params.get("mag_max")
        date_from = request.query_params.get("date_from")
        date_to   = request.query_params.get("date_to")
        sort_by   = request.query_params.get("sort", "-time")

        if search:
            qs = qs.filter(
                Q(place__icontains=search) | Q(earthquake_id__icontains=search)
            )
        if mag_min:
            try:
                qs = qs.filter(magnitude__gte=float(mag_min))
            except ValueError:
                return Response(
                    {"error": "mag_min must be a number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if mag_max:
            try:
                qs = qs.filter(magnitude__lte=float(mag_max))
            except ValueError:
                return Response(
                    {"error": "mag_max must be a number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if date_from:
            qs = qs.filter(time__date__gte=date_from)
        if date_to:
            qs = qs.filter(time__date__lte=date_to)

        allowed_sorts = [
            "time", "-time", "magnitude", "-magnitude",
            "place", "-place", "depth", "-depth",
        ]
        if sort_by not in allowed_sorts:
            sort_by = "-time"
        qs = qs.order_by(sort_by)

        # ── Paginate ──────────────────────────────────────────────────────
        paginator = EarthquakePagination()
        page      = paginator.paginate_queryset(qs, request)
        serializer = EarthquakeSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/earthquakes/<earthquake_id>/
# ─────────────────────────────────────────────────────────────────────────────
class EarthquakeDetailAPIView(APIView):
    """
    GET /api/earthquakes/<earthquake_id>/

    Returns a single earthquake record.

    Response 200:
        { "earthquake_id": "...", "magnitude": 6.5, ... }

    Response 404:
        { "error": "Earthquake not found." }
    """

    def get(self, request, earthquake_id):
        try:
            eq = Earthquake.objects.get(earthquake_id=earthquake_id)
        except Earthquake.DoesNotExist:
            return Response(
                {"error": f"Earthquake '{earthquake_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = EarthquakeSerializer(eq)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/fetch/
# ─────────────────────────────────────────────────────────────────────────────
class FetchEarthquakesAPIView(APIView):
    """
    POST /api/fetch/

    Trigger a USGS earthquake data fetch and store filtered results.

    Request body (JSON):
        {
            "start_date": "2024-01-01",
            "end_date":   "2024-01-31"
        }

    Response 200 (success):
        {
            "message":  "Fetch complete.",
            "fetched":  142,
            "filtered": 8,
            "inserted": 6,
            "skipped":  2,
            "errors":   []
        }

    Response 400 (validation error):
        { "error": "...", "details": {...} }

    Response 500 (unexpected error):
        { "error": "Internal server error.", "detail": "..." }
    """

    def post(self, request):
        serializer = EarthquakeCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input.", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date = str(serializer.validated_data["start_date"])
        end_date   = str(serializer.validated_data["end_date"])

        try:
            result = fetch_and_store(start_date, end_date)
        except Exception as e:
            return Response(
                {"error": "Internal server error.", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if result["errors"]:
            return Response(
                {
                    "message": "Fetch completed with errors.",
                    **result,
                },
                status=status.HTTP_207_MULTI_STATUS,
            )

        return Response(
            {
                "message": "Fetch complete.",
                **result,
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/dashboard/stats/
# ─────────────────────────────────────────────────────────────────────────────
class DashboardStatsAPIView(APIView):
    """
    GET /api/dashboard/stats/

    Returns aggregate statistics for the dashboard.

    Response 200:
        {
            "total_earthquakes": 254,
            "total_users":       3,
            "strongest_mag":     8.1,
            "strongest_place":   "...",
            "latest_time":       "2024-03-15T14:22:00Z",
            "latest_place":      "...",
            "last_fetch":        "2024-03-16T08:00:00Z"
        }
    """

    def get(self, request):
        strongest = Earthquake.objects.order_by("-magnitude").first()
        latest    = Earthquake.objects.order_by("-time").first()
        last_fetch = Earthquake.objects.aggregate(last=Max("fetched_at"))["last"]

        stats = {
            "total_earthquakes": Earthquake.objects.count(),
            "total_users":       AppUser.objects.count(),
            "strongest_mag":     float(strongest.magnitude) if strongest else None,
            "strongest_place":   strongest.place            if strongest else None,
            "latest_time":       latest.time                if latest    else None,
            "latest_place":      latest.place               if latest    else None,
            "last_fetch":        last_fetch,
        }

        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/users/
# ─────────────────────────────────────────────────────────────────────────────
class UserListAPIView(APIView):
    """
    GET /api/users/

    Returns all registered users (passwords excluded).

    Response 200:
        [
            { "user_id": 1, "username": "admin", "email": "...", "created_at": "..." },
            ...
        ]
    """

    def get(self, request):
        users      = AppUser.objects.all()
        serializer = AppUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
