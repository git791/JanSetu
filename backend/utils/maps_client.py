"""
Google Maps Platform wrapper (Distance Matrix API).

Falls back to mock travel-time data when GOOGLE_MAPS_API_KEY is not configured.
"""

from __future__ import annotations

import logging
import math
import os

logger = logging.getLogger(__name__)

_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
_gmaps = None
_MAPS_AVAILABLE = False


def _init_maps() -> None:
    global _gmaps, _MAPS_AVAILABLE

    if not _MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY not set — Maps client using mock fallback.")
        return

    try:
        import googlemaps  # type: ignore

        _gmaps = googlemaps.Client(key=_MAPS_API_KEY)
        _MAPS_AVAILABLE = True
        logger.info("Google Maps client initialised.")
    except Exception as exc:
        logger.warning("Failed to init Google Maps client: %s — using mock fallback.", exc)


_init_maps()


async def get_travel_time(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> dict:
    """
    Return travel distance and duration between two lat/lng points.

    Response shape:
        {
            "distance_km": float,
            "duration_minutes": float,
            "status": "OK" | "MOCK"
        }
    """
    if _MAPS_AVAILABLE and _gmaps is not None:
        try:
            result = _gmaps.distance_matrix(
                origins=[(origin_lat, origin_lng)],
                destinations=[(dest_lat, dest_lng)],
                mode="driving",
                units="metric",
            )
            element = result["rows"][0]["elements"][0]
            if element["status"] == "OK":
                distance_km = element["distance"]["value"] / 1000.0
                duration_min = element["duration"]["value"] / 60.0
                return {
                    "distance_km": round(distance_km, 2),
                    "duration_minutes": round(duration_min, 1),
                    "status": "OK",
                }
        except Exception as exc:
            logger.error("get_travel_time Maps API error: %s — returning mock.", exc)

    # ── Mock fallback: haversine straight-line distance + 1.4× detour factor ──
    return _mock_travel_time(origin_lat, origin_lng, dest_lat, dest_lng)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _mock_travel_time(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> dict:
    """Return a plausible mock travel-time based on straight-line distance."""
    straight_km = _haversine_km(lat1, lng1, lat2, lng2)
    road_km = straight_km * 1.4          # typical urban detour factor
    # Assume average city speed of 20 km/h in Varanasi traffic
    duration_min = (road_km / 20.0) * 60.0
    return {
        "distance_km": round(road_km, 2),
        "duration_minutes": round(duration_min, 1),
        "status": "MOCK",
    }


# ── Geocoding helper ──────────────────────────────────────────────────────────

async def geocode_location(location_str: str) -> dict | None:
    """
    Geocode a location string to lat/lng.
    Returns None if Maps is unavailable.
    """
    if not _MAPS_AVAILABLE or _gmaps is None:
        return None

    try:
        results = _gmaps.geocode(location_str + ", Varanasi, India")
        if results:
            loc = results[0]["geometry"]["location"]
            return {"lat": loc["lat"], "lng": loc["lng"]}
    except Exception as exc:
        logger.error("geocode_location error: %s", exc)

    return None
