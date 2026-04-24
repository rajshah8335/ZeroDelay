"""
Time Engine — calculates the total transit time for each route.

Time formula per segment:
  time = distance / speed + mode_delay

Disruptions multiply the base time by a delay_multiplier.

All logic is pure computation — no external API calls.
"""


def calculate_time(route: dict, cost_config: dict, disruptions: list = None) -> dict:
    """
    Calculate total transit time for a given route.

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

        # Base transit time
        speed = config["speed_kmph"]
        travel_hours = distance / speed if speed > 0 else 0

        # Base delay (loading, customs, etc.)
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
    """
    max_multiplier = 1.0
    route_key1 = f"{from_city}_{to_city}"
    route_key2 = f"{to_city}_{from_city}"

    for d in disruptions:
        if d["mode"] != mode:
            continue
        affected = d["affected_route"]
        if affected in (route_key1, route_key2):
            max_multiplier = max(max_multiplier, d.get("delay_multiplier", 1.0))

    return max_multiplier
