"""
Cost Engine — calculates the total cost for each route.

Cost formulas per mode:
  Road = distance × rate + fuel_surcharge + tolls + loading + unloading + insurance
  Rail = weight × distance × rate + loading + unloading + terminal_handling + insurance
  Sea  = weight × distance × rate + port_handling + customs + insurance

All logic is pure computation — no external API calls.
"""


def calculate_cost(route: dict, weight_kg: float, cost_config: dict) -> dict:
    """
    Calculate the total cost for a given route.

    Args:
        route: route dict with segments from route_engine
        weight_kg: shipment weight in kilograms
        cost_config: pricing parameters loaded from cost_config.json

    Returns:
        dict with per-segment cost breakdown and total cost
    """
    segment_costs = []
    total_cost = 0.0

    for segment in route["segments"]:
        mode = segment["mode"]
        distance = segment["distance_km"]
        config = cost_config[mode]

        if mode == "road":
            cost = _calculate_road_cost(distance, weight_kg, config)
        elif mode == "rail":
            cost = _calculate_rail_cost(distance, weight_kg, config)
        elif mode == "sea":
            cost = _calculate_sea_cost(distance, weight_kg, config)
        elif mode == "air":
            cost = _calculate_air_cost(distance, weight_kg, config)
        else:
            cost = {"total": 0, "breakdown": {}}

        segment_costs.append({
            "mode": mode,
            "from": segment["from"],
            "to": segment["to"],
            "distance_km": distance,
            "cost": cost["total"],
            "breakdown": cost["breakdown"],
        })
        total_cost += cost["total"]

    return {
        "segments": segment_costs,
        "total_cost": round(total_cost, 2),
        "currency": "INR",
    }


def _calculate_road_cost(distance_km: float, weight_kg: float, config: dict) -> dict:
    """
    Road cost = distance × rate + fuel_surcharge + tolls + loading + unloading + insurance.
    Insurance is calculated as a percentage of the base freight cost.
    """
    base_freight = distance_km * config["rate_per_km"]
    fuel_surcharge = distance_km * config["fuel_surcharge_per_km"]
    toll_charges = (distance_km / 100) * config["toll_per_100km"]
    loading = config["loading_charge"]
    unloading = config["unloading_charge"]

    subtotal = base_freight + fuel_surcharge + toll_charges + loading + unloading
    insurance = subtotal * (config["insurance_percent"] / 100)
    total = subtotal + insurance

    return {
        "total": round(total, 2),
        "breakdown": {
            "base_freight": round(base_freight, 2),
            "fuel_surcharge": round(fuel_surcharge, 2),
            "toll_charges": round(toll_charges, 2),
            "loading": loading,
            "unloading": unloading,
            "insurance": round(insurance, 2),
        }
    }


def _calculate_rail_cost(distance_km: float, weight_kg: float, config: dict) -> dict:
    """
    Rail cost = weight × distance × rate + loading + unloading + terminal_handling + insurance.
    """
    base_freight = weight_kg * distance_km * config["rate_per_kg_km"]
    loading = config["loading_charge"]
    unloading = config["unloading_charge"]
    terminal = config["terminal_handling"]

    subtotal = base_freight + loading + unloading + terminal
    insurance = subtotal * (config["insurance_percent"] / 100)
    total = subtotal + insurance

    return {
        "total": round(total, 2),
        "breakdown": {
            "base_freight": round(base_freight, 2),
            "loading": loading,
            "unloading": unloading,
            "terminal_handling": terminal,
            "insurance": round(insurance, 2),
        }
    }


def _calculate_sea_cost(distance_km: float, weight_kg: float, config: dict) -> dict:
    """
    Sea cost = weight × distance × rate + port_handling + customs + insurance.
    """
    base_freight = weight_kg * distance_km * config["rate_per_kg_km"]
    port_handling = config["port_handling_charge"]
    customs = config["customs_clearance"]

    subtotal = base_freight + port_handling + customs
    insurance = subtotal * (config["insurance_percent"] / 100)
    total = subtotal + insurance

    return {
        "total": round(total, 2),
        "breakdown": {
            "base_freight": round(base_freight, 2),
            "port_handling": round(port_handling, 2),
            "customs_clearance": customs,
            "insurance": round(insurance, 2),
        }
    }


def _calculate_air_cost(distance_km: float, weight_kg: float, config: dict) -> dict:
    """
    Air cost = weight × distance × rate + airport_handling + customs + fuel_surcharge + insurance.
    """
    base_freight = weight_kg * distance_km * config["rate_per_kg_km"]
    handling = config["airport_handling_charge"]
    customs = config["customs_clearance"]
    fuel_surcharge = base_freight * (config["fuel_surcharge_percent"] / 100)

    subtotal = base_freight + handling + customs + fuel_surcharge
    insurance = subtotal * (config["insurance_percent"] / 100)
    total = subtotal + insurance

    return {
        "total": round(total, 2),
        "breakdown": {
            "base_freight": round(base_freight, 2),
            "airport_handling": handling,
            "customs_clearance": customs,
            "fuel_surcharge": round(fuel_surcharge, 2),
            "insurance": round(insurance, 2),
        }
    }
