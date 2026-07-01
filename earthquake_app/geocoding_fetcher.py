"""
earthquake_app/geocoding_fetcher.py

Resolves a place name (city / state / country) into latitude & longitude
using the Open-Meteo Geocoding API.

This file does NOT touch the database — it is a pure lookup helper used by
the weather fetch views before calling open_meteo_fetcher.py.
"""
import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def search_locations(query, count=8):
    """
    Search for matching locations by name.

    Returns a list of dicts:
    [
        {
            "name": "New Delhi",
            "country": "India",
            "admin1": "Delhi",          # state/region
            "latitude": 28.6139,
            "longitude": 77.2090,
            "display_name": "New Delhi, Delhi, India"
        },
        ...
    ]
    Returns an empty list if nothing matches or on error.
    """
    if not query or len(query.strip()) < 2:
        return []

    params = {
        "name":     query.strip(),
        "count":    count,
        "language": "en",
        "format":   "json",
    }

    try:
        response = requests.get(GEOCODING_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    results = data.get("results", [])
    locations = []

    for r in results:
        name    = r.get("name", "")
        country = r.get("country", "")
        admin1  = r.get("admin1", "")   # state / province

        parts = [p for p in [name, admin1, country] if p]
        display_name = ", ".join(parts)

        locations.append({
            "name":         name,
            "country":      country,
            "admin1":       admin1,
            "latitude":     r.get("latitude"),
            "longitude":    r.get("longitude"),
            "display_name": display_name,
        })

    return locations