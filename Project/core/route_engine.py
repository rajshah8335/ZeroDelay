"""
Route Engine — generates multi-modal route options using real-time APIs.

Produces three route types between any source and destination worldwide:
  1. Road only (direct trucking via OpenRouteService)
  2. Road + Rail (estimated from road data)
  3. Road + Sea (maritime via searoute library)

Falls back to static JSON data when APIs are unavailable.
"""

from services.maps_service import (
    get_road_info,
    get_sea_distance,
    estimate_rail_info,
    get_air_distance,
)


def generate_routes(
    source: str,
    destination: str,
    source_coords: dict,
    dest_coords: dict,
    routes_data: dict = None,
    nodes: list = None,
) -> list:
    """
    Generate all feasible route options between source and destination.

    Uses real-time APIs first, falls back to static JSON data if unavailable.

    Args:
        source: display name of the origin city
        destination: display name of the destination city
        source_coords: dict with 'lat', 'lng' from geocoding
        dest_coords: dict with 'lat', 'lng' from geocoding
        routes_data: (fallback) distance tables from routes.json
        nodes: (fallback) node list from nodes.json

    Returns:
        list of route dicts, each describing a multi-modal path
    """
    routes = []

    # ---- Attempt real-time data first ----
    road_info = get_road_info(source_coords, dest_coords)
    
    # Try generating live routes (even if road fails, sea might work)
    routes = _generate_live_routes(source, destination, source_coords, dest_coords, road_info)

    # If no live routes were found AND we have fallback data, try the static mode
    if not routes and routes_data and nodes:
        print("[Route Engine] Live APIs returned no routes — falling back to static JSON data")
        source_id = _name_to_id(source, nodes)
        dest_id = _name_to_id(destination, nodes)
        if source_id and dest_id:
            routes = _generate_static_routes(source_id, dest_id, routes_data, nodes)

    return routes


def _generate_live_routes(
    source: str,
    destination: str,
    source_coords: dict,
    dest_coords: dict,
    road_info: dict | None,
) -> list:
    """Generate routes using real-time API data."""
    routes = []

    # ---- Route 1: Direct Road ----
    if road_info:
        routes.append({
            "id": "route_road",
            "name": "Direct Road",
            "type": "road",
            "segments": [
                {
                    "mode": "road",
                    "from": source,
                    "to": destination,
                    "distance_km": road_info["distance_km"],
                    "duration_hours": road_info["duration_hours"],
                }
            ],
            "total_distance_km": road_info["distance_km"],
            "data_source": "openrouteservice",
        })

        # ---- Route 2: Road + Rail (estimated) ----
        rail_info = estimate_rail_info(road_info)
        if rail_info:
            routes.append({
                "id": "route_rail",
                "name": "Road + Rail",
                "type": "road_rail",
                "segments": [
                    {
                        "mode": "rail",
                        "from": source,
                        "to": destination,
                        "distance_km": rail_info["distance_km"],
                        "duration_hours": rail_info["duration_hours"],
                    }
                ],
                "total_distance_km": rail_info["distance_km"],
                "data_source": "estimated_from_road",
            })

    # ---- Route 3: Road + Sea ----
    sea_info = get_sea_distance(source_coords, dest_coords)
    if sea_info and sea_info["distance_km"] > 0:
        # Sea speed from cost_config: ~25 kmph + 24h port delay
        sea_duration = sea_info["distance_km"] / 25  # rough estimate in hours
        routes.append({
            "id": "route_sea",
            "name": "Road + Sea",
            "type": "road_sea",
            "segments": [
                {
                    "mode": "sea",
                    "from": source,
                    "to": destination,
                    "distance_km": sea_info["distance_km"],
                    "duration_hours": round(sea_duration, 2),
                }
            ],
            "total_distance_km": sea_info["distance_km"],
            "data_source": "searoute",
        })

    # ---- Route 4: Air Freight ----
    air_info = get_air_distance(source_coords, dest_coords)
    if air_info and air_info["distance_km"] > 0:
        # Air speed from cost_config: ~800 kmph + 8h hub delay
        air_duration = air_info["distance_km"] / 800
        routes.append({
            "id": "route_air",
            "name": "Direct Air",
            "type": "air",
            "segments": [
                {
                    "mode": "air",
                    "from": source,
                    "to": destination,
                    "distance_km": air_info["distance_km"],
                    "duration_hours": round(air_duration, 2),
                }
            ],
            "total_distance_km": air_info["distance_km"],
            "data_source": "haversine_calculation",
        })

    return routes


# =====================
# STATIC JSON FALLBACK
# =====================

def _generate_static_routes(source: str, destination: str, routes_data: dict, nodes: list) -> list:
    """
    Fallback: Generate routes from static JSON data (original logic).
    Used when real-time APIs are unavailable.
    """
    node_map = {n["id"]: n for n in nodes}
    routes = []

    # ---- Route 1: Road Only ----
    road_dist = _get_distance(source, destination, routes_data.get("road_distances", {}))
    if road_dist:
        routes.append({
            "id": "route_road",
            "name": "Direct Road",
            "type": "road",
            "segments": [
                {
                    "mode": "road",
                    "from": source,
                    "to": destination,
                    "distance_km": road_dist,
                }
            ],
            "total_distance_km": road_dist,
            "data_source": "static_json",
        })

    # ---- Route 2: Road + Rail ----
    rail_route = _build_static_rail_route(source, destination, routes_data, node_map)
    if rail_route:
        routes.append(rail_route)

    # ---- Route 3: Road + Sea ----
    sea_route = _build_static_sea_route(source, destination, routes_data, node_map)
    if sea_route:
        routes.append(sea_route)

    return routes


def _build_static_rail_route(source: str, destination: str, routes_data: dict, node_map: dict) -> dict | None:
    """Fallback: Build Rail route from static JSON data."""
    rail_distances = routes_data.get("rail_distances", {})
    road_distances = routes_data.get("road_distances", {})
    nearest_rail = routes_data.get("nearest_rail_hub", {})

    src_rail = source if node_map.get(source, {}).get("has_rail_terminal") else nearest_rail.get(source)
    dst_rail = destination if node_map.get(destination, {}).get("has_rail_terminal") else nearest_rail.get(destination)

    if not src_rail or not dst_rail:
        return None

    rail_dist = _get_distance(src_rail, dst_rail, rail_distances)
    if not rail_dist:
        return None

    segments = []
    total_dist = 0

    if src_rail != source:
        first_mile = _get_distance(source, src_rail, road_distances)
        if not first_mile:
            return None
        segments.append({"mode": "road", "from": source, "to": src_rail, "distance_km": first_mile})
        total_dist += first_mile

    segments.append({"mode": "rail", "from": src_rail, "to": dst_rail, "distance_km": rail_dist})
    total_dist += rail_dist

    if dst_rail != destination:
        last_mile = _get_distance(dst_rail, destination, road_distances)
        if not last_mile:
            return None
        segments.append({"mode": "road", "from": dst_rail, "to": destination, "distance_km": last_mile})
        total_dist += last_mile

    return {
        "id": "route_rail",
        "name": "Road + Rail",
        "type": "road_rail",
        "segments": segments,
        "total_distance_km": total_dist,
        "data_source": "static_json",
    }


def _build_static_sea_route(source: str, destination: str, routes_data: dict, node_map: dict) -> dict | None:
    """Fallback: Build Sea route from static JSON data."""
    sea_distances = routes_data.get("sea_distances", {})
    road_distances = routes_data.get("road_distances", {})
    nearest_port = routes_data.get("nearest_port", {})

    src_port = source if node_map.get(source, {}).get("has_port") else nearest_port.get(source)
    dst_port = destination if node_map.get(destination, {}).get("has_port") else nearest_port.get(destination)

    if not src_port or not dst_port:
        return None
    if src_port == dst_port:
        return None

    sea_dist = _get_distance(src_port, dst_port, sea_distances)
    if not sea_dist:
        return None

    segments = []
    total_dist = 0

    if src_port != source:
        first_mile = _get_distance(source, src_port, road_distances)
        if not first_mile:
            return None
        segments.append({"mode": "road", "from": source, "to": src_port, "distance_km": first_mile})
        total_dist += first_mile

    segments.append({"mode": "sea", "from": src_port, "to": dst_port, "distance_km": sea_dist})
    total_dist += sea_dist

    if dst_port != destination:
        last_mile = _get_distance(dst_port, destination, road_distances)
        if not last_mile:
            return None
        segments.append({"mode": "road", "from": dst_port, "to": destination, "distance_km": last_mile})
        total_dist += last_mile

    return {
        "id": "route_sea",
        "name": "Road + Sea",
        "type": "road_sea",
        "segments": segments,
        "total_distance_km": total_dist,
        "data_source": "static_json",
    }


# =====================
# UTILITY FUNCTIONS
# =====================

def _get_distance(city_a: str, city_b: str, distance_table: dict) -> float | None:
    """Look up distance between two cities (tries both key orderings)."""
    key1 = f"{city_a}_{city_b}"
    key2 = f"{city_b}_{city_a}"
    return distance_table.get(key1) or distance_table.get(key2)


def _name_to_id(city_name: str, nodes: list) -> str | None:
    """
    Convert a city display name to its node ID for static JSON lookup.
    Tries case-insensitive matching against node names and IDs.
    """
    name_lower = city_name.lower().strip()
    for node in nodes:
        if node["name"].lower() == name_lower or node["id"].lower() == name_lower:
            return node["id"]
    return None
