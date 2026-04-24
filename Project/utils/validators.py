"""
Request validation utility.
Validates incoming API payloads before they reach the core logic.

Now supports worldwide cities — validation only checks that fields
are non-empty and within acceptable ranges. City existence is
verified during the geocoding step in the API layer.
"""


def validate_route_request(data: dict) -> tuple[dict | None, str | None]:
    """
    Validate the POST /api/routes request body.

    Returns:
        (cleaned_data, None) on success
        (None, error_message) on failure
    """
    if not data:
        return None, "Request body is required"

    # --- Source validation ---
    source = data.get("source", "").strip() if isinstance(data.get("source"), str) else ""
    if not source:
        return None, "Field 'source' is required (any city name worldwide)"

    # --- Destination validation ---
    destination = data.get("destination", "").strip() if isinstance(data.get("destination"), str) else ""
    if not destination:
        return None, "Field 'destination' is required (any city name worldwide)"

    # Basic same-city check (case-insensitive)
    if source.lower() == destination.lower():
        return None, "Source and destination cannot be the same"

    # --- Weight validation ---
    weight = data.get("weight")
    if weight is None:
        return None, "Field 'weight' is required (in kg)"
    try:
        weight = float(weight)
    except (TypeError, ValueError):
        return None, "'weight' must be a numeric value"
    if weight <= 0:
        return None, "'weight' must be positive"
    if weight > 100000:
        return None, "'weight' cannot exceed 100,000 kg"

    # --- Priority validation ---
    priority = data.get("priority", 0.5)
    try:
        priority = float(priority)
    except (TypeError, ValueError):
        return None, "'priority' must be a numeric value between 0 and 1"
    if not (0.0 <= priority <= 1.0):
        return None, "'priority' must be between 0.0 (cost-first) and 1.0 (time-first)"

    cleaned = {
        "source": source,
        "destination": destination,
        "weight": weight,
        "priority": priority,
    }
    return cleaned, None
