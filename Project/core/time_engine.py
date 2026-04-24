"""
Time Engine — calculates the total transit time for each route.

For live API routes:
  - Road: Uses real driving time from OpenRouteService (if available in segment)
  - Rail: Uses estimated duration from maps_service
  - Sea:  Uses estimated duration from route_engine

For static fallback routes:
  - time = distance / speed + mode_delay

Disruptions multiply the base time by a delay_multiplier.

All logic is pure computation — no external API calls.
"""


def calculate_time(route: dict, cost_config: dict, disruptions: list = None) -> dict:
    """
    Calculate total transit time for a given route.

    Supports both live API segments (with pre-calculated duration_hours)
    and static segments (calculated from distance/speed).

    Args:
        route: route dict with segments from route_engine
        cost_config: contains speed and base delay per mode
        disruptions: active disruptions that may affect timing

    Returns:
        dict with per-segment time breakdown and total hours
    """
    if disruptions is None:
        disruptions = []

    segment_times = []
    total_hours = 0.0

    for segment in route["segments"]:
        mode = segment["mode"]
        distance = segment["distance_km"]
        config = cost_config[mode]

        # Check if real duration was already computed by the API
        if "duration_hours" in segment and segment["duration_hours"]:
            travel_hours = segment["duration_hours"]
        else:
            # Fallback: calculate from distance and speed
            speed = config["speed_kmph"]
            travel_hours = distance / speed if speed > 0 else 0

        # Base delay (loading, customs, terminal handling, etc.)
        base_delay = config["delay_hours"]

        # Check for disruptions on this segment
        disruption_multiplier = _get_disruption_multiplier(
            segment["from"], segment["to"], mode, disruptions
        )

        # Apply disruption to travel time
        adjusted_travel = travel_hours * disruption_multiplier
        total_segment_hours = adjusted_travel + base_delay

        segment_times.append({
            "mode": mode,
            "from": segment["from"],
            "to": segment["to"],
            "distance_km": distance,
            "travel_hours": round(travel_hours, 2),
            "delay_hours": base_delay,
            "disruption_multiplier": disruption_multiplier,
            "total_hours": round(total_segment_hours, 2),
            "uses_real_time": "duration_hours" in segment,
        })
        total_hours += total_segment_hours

    return {
        "segments": segment_times,
        "total_hours": round(total_hours, 2),
        "total_days": round(total_hours / 24, 1),
    }


def _get_disruption_multiplier(from_city: str, to_city: str, mode: str, disruptions: list) -> float:
    """
    Check if any active disruption affects this segment.
    Returns the worst-case delay multiplier (highest if multiple match).

    For worldwide cities, disruptions are matched case-insensitively
    and with underscored key format.
    """
    max_multiplier = 1.0

    # Normalize city names for matching (lowercase, spaces → underscores)
    from_norm = from_city.lower().replace(" ", "_")
    to_norm = to_city.lower().replace(" ", "_")
    route_key1 = f"{from_norm}_{to_norm}"
    route_key2 = f"{to_norm}_{from_norm}"

    for d in disruptions:
        if d["mode"] != mode:
            continue
        affected = d["affected_route"].lower()
        if affected in (route_key1, route_key2):
            max_multiplier = max(max_multiplier, d.get("delay_multiplier", 1.0))

    return max_multiplier
