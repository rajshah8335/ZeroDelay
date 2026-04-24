"""
Maps Service — real-time geocoding, road, and sea distance calculations.

Uses free APIs:
  - Geocoding: geopy + Nominatim (OpenStreetMap, free, 1 req/sec)
  - Road:      OpenRouteService Directions API (free, 2000 req/day)
  - Sea:       searoute Python library (free, offline, unlimited)
  - Rail:      Estimated from road distance × config factor

All functions include try/except with graceful fallback.
"""

import openrouteservice
import searoute as sr
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from functools import lru_cache
import math

import config


# ---- Initialize clients ----

# Nominatim geocoder (free, OpenStreetMap-based)
_geolocator = Nominatim(user_agent=config.GEOCODER_USER_AGENT, timeout=config.API_TIMEOUT)
_geocode = RateLimiter(_geolocator.geocode, min_delay_seconds=1.1)

# OpenRouteService client (free tier: 2000 directions/day)
_ors_client = None
if config.ORS_API_KEY and config.ORS_API_KEY != "your_openrouteservice_api_key_here":
    try:
        _ors_client = openrouteservice.Client(
            key=config.ORS_API_KEY,
            timeout=config.API_TIMEOUT,
        )
    except Exception as e:
        print(f"[Maps Service] Failed to initialize ORS client: {e}")


# =====================
# GEOCODING
# =====================

@lru_cache(maxsize=256)
def geocode_city(city_name: str) -> dict | None:
    """
    Convert a city name to lat/lng coordinates using Nominatim (OpenStreetMap).

    Args:
        city_name: human-readable city name (e.g., "London", "Mumbai", "New York")

    Returns:
        dict with 'lat', 'lng', 'display_name' or None if not found
    """
    try:
        location = _geocode(city_name)
        if location:
            return {
                "lat": location.latitude,
                "lng": location.longitude,
                "display_name": location.address,
            }
        print(f"[Maps Service] Geocoding failed: '{city_name}' not found")
        return None
    except Exception as e:
        print(f"[Maps Service] Geocoding error for '{city_name}': {e}")
        return None


# =====================
# ROAD DISTANCE
# =====================

def get_road_info(origin_coords: dict, dest_coords: dict) -> dict | None:
    """
    Get real driving distance (km) and time (hours) using OpenRouteService.

    Args:
        origin_coords: dict with 'lat', 'lng'
        dest_coords: dict with 'lat', 'lng'

    Returns:
        dict with 'distance_km' and 'duration_hours', or None on failure
    """
    if not _ors_client:
        return None

    try:
        # ORS expects coordinates as [longitude, latitude]
        coords = [
            [origin_coords["lng"], origin_coords["lat"]],
            [dest_coords["lng"], dest_coords["lat"]],
        ]

        result = _ors_client.directions(
            coordinates=coords,
            profile="driving-hgv",  # Heavy goods vehicle (truck) profile
            format="json",
        )

        if result and "routes" in result and len(result["routes"]) > 0:
            route = result["routes"][0]["summary"]
            distance_km = route["distance"] / 1000  # meters → km
            duration_hours = route["duration"] / 3600  # seconds → hours
            return {
                "distance_km": round(distance_km, 1),
                "duration_hours": round(duration_hours, 2),
            }

        return None
    except Exception as e:
        print(f"[Maps Service] ORS road distance error: {e}")
        return None


# =====================
# SEA DISTANCE
# =====================

def get_sea_distance(origin_coords: dict, dest_coords: dict) -> dict | None:
    """
    Calculate maritime route distance using the searoute library (offline, free).

    The library automatically handles land-to-sea snapping — if a point is
    inland, it finds the nearest coastal point.

    Args:
        origin_coords: dict with 'lat', 'lng'
        dest_coords: dict with 'lat', 'lng'

    Returns:
        dict with 'distance_km', or None on failure
    """
    try:
        # searoute expects [longitude, latitude] format
        origin = [origin_coords["lng"], origin_coords["lat"]]
        destination = [dest_coords["lng"], dest_coords["lat"]]

        route = sr.searoute(origin, destination, units="km")

        if route and hasattr(route, "properties"):
            distance_km = route.properties.get("length", 0)
            return {
                "distance_km": round(distance_km, 1),
            }

        return None
    except Exception as e:
        print(f"[Maps Service] Sea route calculation error: {e}")
        return None


# =====================
# RAIL DISTANCE (Estimated)
# =====================

def estimate_rail_info(road_info: dict) -> dict | None:
    """
    Estimate rail distance and time from road data.

    No free global rail freight API exists, so we estimate:
      - Rail distance ≈ road distance × 1.1 (rail tracks take longer paths)
      - Rail time ≈ road driving time × 0.85 (trains are faster overall)

    Args:
        road_info: dict with 'distance_km' and 'duration_hours' from get_road_info()

    Returns:
        dict with estimated 'distance_km' and 'duration_hours', or None
    """
    if not road_info:
        return None

    return {
        "distance_km": round(road_info["distance_km"] * config.RAIL_DISTANCE_FACTOR, 1),
        "duration_hours": round(road_info["duration_hours"] * config.RAIL_TIME_FACTOR, 2),
    }


# =====================
# COASTAL CHECK
# =====================

def is_coastal_viable(origin_coords: dict, dest_coords: dict) -> bool:
    """
    Quick check if a sea route between two points is likely viable.
    Returns False if both points are deep inland on the same continent
    and the sea distance would be unreasonably long.
    """
    sea_info = get_sea_distance(origin_coords, dest_coords)
    if not sea_info:
        return False

    # If searoute returns a valid distance, the route is viable
    return sea_info["distance_km"] > 0


def get_air_distance(origin_coords: dict, dest_coords: dict) -> dict:
    """
    Calculate Great Circle distance (km) between two coordinates using Haversine formula.
    Used for Air Freight.
    """
    lat1, lon1 = math.radians(origin_coords["lat"]), math.radians(origin_coords["lng"])
    lat2, lon2 = math.radians(dest_coords["lat"]), math.radians(dest_coords["lng"])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    distance_km = c * r
    return {"distance_km": round(distance_km, 1)}
