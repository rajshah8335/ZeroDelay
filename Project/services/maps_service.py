"""
Maps Service — mock implementation for distance and geocoding lookups.

In production, this would integrate with Google Maps or similar.
Currently serves as a placeholder that the route engine can optionally use.
"""


def get_road_distance(source: str, destination: str) -> float | None:
    """
    Mock: Get driving distance between two cities in km.
    In production, would call Google Maps Distance Matrix API.

    Returns None to indicate we should fall back to the static data.
    """
    # Placeholder — real implementation would call an external mapping API
    return None


def get_coordinates(city_name: str) -> dict | None:
    """
    Mock: Geocode a city name to lat/lng.
    In production, would call Google Maps Geocoding API.
    """
    # Placeholder
    return None


def estimate_road_time(source: str, destination: str) -> float | None:
    """
    Mock: Estimate driving time between two cities in hours.
    In production, would call Google Maps Directions API with traffic data.
    """
    # Placeholder
    return None
