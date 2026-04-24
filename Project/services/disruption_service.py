"""
Disruption Service — loads and filters active disruptions.

Applies disruption effects (delay & cost multipliers) to route calculations.
Data is loaded from disruptions.json.
"""

from datetime import datetime, date

from utils.loader import load_disruptions
import config


def get_active_disruptions() -> list:
    """
    Retrieve all currently active disruptions.
    Filters by valid_from and valid_until dates.
    """
    all_disruptions = load_disruptions(config.DISRUPTIONS_FILE)
    today = date.today()

    active = []
    for d in all_disruptions:
        valid_from = _parse_date(d.get("valid_from"))
        valid_until = _parse_date(d.get("valid_until"))

        # Include if within active window (or if dates are missing, include anyway)
        if valid_from and today < valid_from:
            continue
        if valid_until and today > valid_until:
            continue
        active.append(d)

    return active


def get_disruptions_for_route(from_city: str, to_city: str, mode: str) -> list:
    """
    Get disruptions specifically affecting a given segment.
    """
    active = get_active_disruptions()
    route_key1 = f"{from_city}_{to_city}"
    route_key2 = f"{to_city}_{from_city}"

    matching = []
    for d in active:
        if d["mode"] != mode:
            continue
        if d["affected_route"] in (route_key1, route_key2):
            matching.append(d)

    return matching


def get_cost_multiplier(from_city: str, to_city: str, mode: str) -> float:
    """
    Get the aggregate cost multiplier for a disrupted segment.
    Returns 1.0 if no disruption affects this segment.
    """
    disruptions = get_disruptions_for_route(from_city, to_city, mode)
    if not disruptions:
        return 1.0

    # Use the worst-case multiplier
    return max(d.get("cost_multiplier", 1.0) for d in disruptions)


def _parse_date(date_str: str) -> date | None:
    """Parse an ISO date string (YYYY-MM-DD) to a date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None
