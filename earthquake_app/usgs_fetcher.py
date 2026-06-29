"""
earthquake_app/usgs_fetcher.py
================================
Core USGS API integration — refactored from the original standalone script
so it works as a reusable module inside Django.

PUBLIC FUNCTION:
    fetch_and_store(start_date, end_date)
        → {"fetched": N, "inserted": N, "skipped": N, "errors": [...]}

FILTERING RULE:  magnitude >= 6.0
"""

import requests
import datetime as dt
from django.db import IntegrityError, DatabaseError

from .models import Earthquake

# ── Constants ─────────────────────────────────────────────────────────────────
USGS_API_URL    = "https://earthquake.usgs.gov/fdsnws/event/1/query"
MIN_MAGNITUDE   = 6.0
REQUEST_TIMEOUT = 30   # seconds


# ─────────────────────────────────────────────────────────────────────────────
def fetch_from_usgs(start_date: str, end_date: str) -> list:
    """
    Call the USGS GeoJSON feed and return raw feature list.

    Args:
        start_date: "YYYY-MM-DD"
        end_date:   "YYYY-MM-DD"

    Returns:
        List of GeoJSON feature dicts.

    Raises:
        ValueError:   if dates are invalid or end < start
        RuntimeError: on network / HTTP errors
    """
    try:
        start = dt.datetime.strptime(start_date, "%Y-%m-%d")
        end   = dt.datetime.strptime(end_date,   "%Y-%m-%d")
    except ValueError:
        raise ValueError("Dates must be in YYYY-MM-DD format.")

    if end < start:
        raise ValueError("End date must be on or after start date.")

    params = {
        "format":    "geojson",
        "starttime": start_date,
        "endtime":   end_date,
    }

    try:
        response = requests.get(USGS_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("USGS API request timed out. Check your internet connection.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot connect to USGS API. Check your internet connection.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"USGS API returned an error: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error: {e}")

    data = response.json()
    return data.get("features", [])


# ─────────────────────────────────────────────────────────────────────────────
def parse_feature(feature: dict):
    """
    Extract and clean fields from a single GeoJSON feature.

    Returns a dict ready for Earthquake model construction,
    or None if the feature should be skipped (magnitude < 6.0).
    """
    props  = feature.get("properties", {})
    geo    = feature.get("geometry", {})
    coords = geo.get("coordinates") or [None, None, None]

    mag = props.get("mag")
    if mag is None or float(mag) < MIN_MAGNITUDE:
        return None   # filtered out

    # Convert epoch-milliseconds UTC → timezone-aware datetime
    raw_time = props.get("time")
    eq_time  = None
    if raw_time is not None:
        eq_time = dt.datetime.utcfromtimestamp(raw_time / 1000).replace(
            tzinfo=dt.timezone.utc
        )

    return {
        "earthquake_id": feature.get("id"),
        "magnitude":     float(mag),
        "place":         props.get("place"),
        "time":          eq_time,
        "longitude":     float(coords[0]) if coords[0] is not None else None,
        "latitude":      float(coords[1]) if coords[1] is not None else None,
        "depth":         float(coords[2]) if coords[2] is not None else None,
        "url":           props.get("url"),
    }


# ─────────────────────────────────────────────────────────────────────────────
def fetch_and_store(start_date: str, end_date: str) -> dict:
    """
    Full pipeline: fetch → filter → store → return summary.

    Args:
        start_date: "YYYY-MM-DD"
        end_date:   "YYYY-MM-DD"

    Returns:
        {
            "fetched":  total records from API,
            "filtered": records after mag >= 6 filter,
            "inserted": new records saved to DB,
            "skipped":  duplicate records,
            "errors":   list of error strings,
        }
    """
    summary = {"fetched": 0, "filtered": 0, "inserted": 0, "skipped": 0, "errors": []}

    # Step 1: Fetch from USGS
    try:
        features = fetch_from_usgs(start_date, end_date)
    except (ValueError, RuntimeError) as e:
        summary["errors"].append(str(e))
        return summary

    summary["fetched"] = len(features)

    # Step 2: Parse + filter
    records = []
    for feature in features:
        parsed = parse_feature(feature)
        if parsed:
            records.append(parsed)

    summary["filtered"] = len(records)

    # Step 3: Insert into MySQL using get_or_create (prevents duplicates)
    for rec in records:
        try:
            _, created = Earthquake.objects.get_or_create(
                earthquake_id=rec["earthquake_id"],
                defaults={k: v for k, v in rec.items() if k != "earthquake_id"},
            )
            if created:
                summary["inserted"] += 1
            else:
                summary["skipped"] += 1
        except (IntegrityError, DatabaseError) as e:
            summary["errors"].append(f"DB error for {rec.get('earthquake_id')}: {e}")

    return summary
