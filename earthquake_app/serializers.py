"""
earthquake_app/serializers.py
DRF serializers for JSON API responses.
"""
from rest_framework import serializers
from .models import Earthquake, AppUser


class EarthquakeSerializer(serializers.ModelSerializer):
    """Full earthquake serializer for list and detail endpoints."""

    class Meta:
        model  = Earthquake
        fields = [
            "earthquake_id", "magnitude", "place", "time",
            "latitude", "longitude", "depth", "url", "fetched_at",
        ]
        read_only_fields = ["fetched_at"]


class EarthquakeCreateSerializer(serializers.Serializer):
    """
    Input serializer for the POST /api/fetch/ endpoint.
    Validates start_date and end_date then delegates to usgs_fetcher.
    """
    start_date = serializers.DateField(
        help_text="Fetch start date (YYYY-MM-DD)"
    )
    end_date   = serializers.DateField(
        help_text="Fetch end date (YYYY-MM-DD)"
    )

    def validate(self, data):
        if data["end_date"] < data["start_date"]:
            raise serializers.ValidationError("end_date must be >= start_date.")
        return data


class AppUserSerializer(serializers.ModelSerializer):
    """Safe user serializer — never exposes password."""

    class Meta:
        model  = AppUser
        fields = ["user_id", "username", "email", "created_at"]


class DashboardStatsSerializer(serializers.Serializer):
    """Stats returned by GET /api/dashboard/stats/."""
    total_earthquakes  = serializers.IntegerField()
    total_users        = serializers.IntegerField()
    strongest_mag      = serializers.FloatField(allow_null=True)
    strongest_place    = serializers.CharField(allow_null=True)
    latest_time        = serializers.DateTimeField(allow_null=True)
    latest_place       = serializers.CharField(allow_null=True)
    last_fetch         = serializers.DateTimeField(allow_null=True)
