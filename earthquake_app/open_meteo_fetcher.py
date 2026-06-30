"""
earthquake_app/open_meteo_fetcher.py

Fetches weather data from Open-Meteo APIs and stores it in the database.

Two data sources:
  - Archive API   (historical / past weather)
  - Forecast API  (future weather, up to 16 days ahead)

Users never call these APIs directly — only this file does, then results
are saved to WeatherRecord and read from the database afterwards.
"""
import requests
from .models import WeatherRecord

ARCHIVE_URL  = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_PARAMS = "temperature_2m_max,temperature_2m_min,precipitation_sum"


# ─────────────────────────────────────────────────────────────────────────
# HISTORICAL (PAST) WEATHER
# ─────────────────────────────────────────────────────────────────────────

def fetch_from_open_meteo(start_date, end_date, latitude, longitude):
    params = {
        "latitude":   latitude,
        "longitude":  longitude,
        "start_date": start_date,
        "end_date":   end_date,
        "daily":      DAILY_PARAMS,
        "timezone":   "auto",
    }
    response = requests.get(ARCHIVE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_daily_records(api_data, latitude, longitude, location_name=None):
    daily   = api_data.get("daily", {})
    dates   = daily.get("time", [])
    t_max   = daily.get("temperature_2m_max", [])
    t_min   = daily.get("temperature_2m_min", [])
    precip  = daily.get("precipitation_sum", [])

    records = []
    for i, date in enumerate(dates):
        records.append({
            "date":              date,
            "latitude":          latitude,
            "longitude":         longitude,
            "location_name":     location_name,
            "temperature_max":   t_max[i]  if i < len(t_max)  else None,
            "temperature_min":   t_min[i]  if i < len(t_min)  else None,
            "precipitation_sum": precip[i] if i < len(precip) else None,
        })
    return records


def fetch_and_store_weather(start_date, end_date, latitude, longitude, location_name=None):
    """Fetches PAST weather and stores it with data_type='historical'."""
    result = {
        "fetched":  0,
        "inserted": 0,
        "skipped":  0,
        "errors":   [],
    }
    try:
        api_data = fetch_from_open_meteo(start_date, end_date, latitude, longitude)
        records  = parse_daily_records(api_data, latitude, longitude, location_name)
        result["fetched"] = len(records)

        for rec in records:
            try:
                obj, created = WeatherRecord.objects.get_or_create(
                    latitude=rec["latitude"],
                    longitude=rec["longitude"],
                    date=rec["date"],
                    data_type="historical",
                    defaults={
                        "location_name":     rec["location_name"],
                        "temperature_max":   rec["temperature_max"],
                        "temperature_min":   rec["temperature_min"],
                        "precipitation_sum": rec["precipitation_sum"],
                    }
                )
                if created:
                    result["inserted"] += 1
                else:
                    result["skipped"] += 1
            except Exception as e:
                result["errors"].append(str(e))

    except Exception as e:
        result["errors"].append(f"API Error: {str(e)}")

    return result


# ─────────────────────────────────────────────────────────────────────────
# FORECAST (FUTURE) WEATHER — up to 16 days ahead
# ─────────────────────────────────────────────────────────────────────────

def fetch_from_open_meteo_forecast(latitude, longitude, forecast_days=7):
    forecast_days = max(1, min(int(forecast_days), 16))  # clamp 1-16
    params = {
        "latitude":      latitude,
        "longitude":     longitude,
        "daily":         DAILY_PARAMS,
        "forecast_days": forecast_days,
        "timezone":      "auto",
    }
    response = requests.get(FORECAST_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_and_store_forecast(latitude, longitude, forecast_days=7, location_name=None):
    """Fetches FUTURE weather and stores it with data_type='forecast'."""
    result = {
        "fetched":  0,
        "inserted": 0,
        "skipped":  0,
        "errors":   [],
    }
    try:
        api_data = fetch_from_open_meteo_forecast(latitude, longitude, forecast_days)
        records  = parse_daily_records(api_data, latitude, longitude, location_name)
        result["fetched"] = len(records)

        for rec in records:
            try:
                obj, created = WeatherRecord.objects.get_or_create(
                    latitude=rec["latitude"],
                    longitude=rec["longitude"],
                    date=rec["date"],
                    data_type="forecast",
                    defaults={
                        "location_name":     rec["location_name"],
                        "temperature_max":   rec["temperature_max"],
                        "temperature_min":   rec["temperature_min"],
                        "precipitation_sum": rec["precipitation_sum"],
                    }
                )
                if created:
                    result["inserted"] += 1
                else:
                    result["skipped"] += 1
            except Exception as e:
                result["errors"].append(str(e))

    except Exception as e:
        result["errors"].append(f"API Error: {str(e)}")

    return result