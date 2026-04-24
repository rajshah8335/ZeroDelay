"""
Request validation utility.
Validates incoming API payloads before they reach the core logic.
"""


# Supported city names (lowercase for matching)
SUPPORTED_CITIES = {
    "pune", "mumbai", "chennai", "delhi", "bangalore",
    "kolkata", "hyderabad", "ahmedabad", "jaipur",
    "cochin", "visakhapatnam", "vizag", "goa"
}

# Aliases to canonical node IDs
CITY_ALIASES = {
    "visakhapatnam": "vizag",
    "kochi": "cochin",
    "bengaluru": "bangalore",
    "new delhi": "delhi",
    "calcutta": "kolkata",
    "bombay": "mumbai",
    "madras": "chennai",
}


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
    source = data.get("source", "").strip()
    if not source:
        return None, "Field 'source' is required"

    # --- Destination validation ---
    destination = data.get("destination", "").strip()
    if not destination:
        return None, "Field 'destination' is required"

    # Normalize city names
    source = _normalize_city(source)
    destination = _normalize_city(destination)

    if source not in SUPPORTED_CITIES:
        return None, f"Unsupported source city: '{data.get('source')}'"
    if destination not in SUPPORTED_CITIES:
        return None, f"Unsupported destination city: '{data.get('destination')}'"
    if source == destination:
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

    # Resolve aliases to canonical IDs
    source_id = CITY_ALIASES.get(source, source)
    destination_id = CITY_ALIASES.get(destination, destination)

    cleaned = {
        "source": source_id,
        "destination": destination_id,
        "weight": weight,
        "priority": priority,
    }
    return cleaned, None


def _normalize_city(name: str) -> str:
    """Lowercase and strip a city name for matching."""
    return name.lower().strip()
