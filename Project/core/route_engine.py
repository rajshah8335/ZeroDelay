"""
Route Engine — generates multi-modal route options.

Produces three route types between any source and destination:
  1. Road only (direct trucking)
  2. Road + Rail (truck to rail terminal, rail, truck from rail terminal)
  3. Road + Sea (truck to port, sea freight, truck from port)

All logic is pure computation — no external API calls.
"""


def generate_routes(source: str, destination: str, routes_data: dict, nodes: list) -> list:
    """
    Generate all feasible route options between source and destination.

    Args:
        source: canonical node ID of the origin city
        destination: canonical node ID of the destination city
        routes_data: distance tables loaded from routes.json
        nodes: list of node dicts loaded from nodes.json

    Returns:
        list of route dicts, each describing a multi-modal path
    """
    node_map = {n["id"]: n for n in nodes}
    routes = []

    # ---- Route 1: Road Only ----
    road_dist = _get_distance(source, destination, routes_data["road_distances"])
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
        })

    # ---- Route 2: Road + Rail ----
    rail_route = _build_rail_route(source, destination, routes_data, node_map)
    if rail_route:
        routes.append(rail_route)

    # ---- Route 3: Road + Sea ----
    sea_route = _build_sea_route(source, destination, routes_data, node_map)
    if sea_route:
        routes.append(sea_route)

    return routes


def _build_rail_route(source: str, destination: str, routes_data: dict, node_map: dict) -> dict | None:
    """
    Build a Road→Rail→Road route.
    If source/destination lacks a rail terminal, route through the nearest hub.
    """
    rail_distances = routes_data.get("rail_distances", {})
    road_distances = routes_data.get("road_distances", {})
    nearest_rail = routes_data.get("nearest_rail_hub", {})

    # Determine rail boarding and alighting points
    src_rail = source if node_map.get(source, {}).get("has_rail_terminal") else nearest_rail.get(source)
    dst_rail = destination if node_map.get(destination, {}).get("has_rail_terminal") else nearest_rail.get(destination)

    if not src_rail or not dst_rail:
        return None

    # Get rail distance
    rail_dist = _get_distance(src_rail, dst_rail, rail_distances)
    if not rail_dist:
        return None

    segments = []
    total_dist = 0

    # First-mile road leg (if needed)
    if src_rail != source:
        first_mile = _get_distance(source, src_rail, road_distances)
        if not first_mile:
            return None
        segments.append({"mode": "road", "from": source, "to": src_rail, "distance_km": first_mile})
        total_dist += first_mile

    # Rail segment
    segments.append({"mode": "rail", "from": src_rail, "to": dst_rail, "distance_km": rail_dist})
    total_dist += rail_dist

    # Last-mile road leg (if needed)
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
    }


def _build_sea_route(source: str, destination: str, routes_data: dict, node_map: dict) -> dict | None:
    """
    Build a Road→Sea→Road route.
    If source/destination is landlocked, route through the nearest port city.
    """
    sea_distances = routes_data.get("sea_distances", {})
    road_distances = routes_data.get("road_distances", {})
    nearest_port = routes_data.get("nearest_port", {})

    # Determine port boarding and alighting points
    src_port = source if node_map.get(source, {}).get("has_port") else nearest_port.get(source)
    dst_port = destination if node_map.get(destination, {}).get("has_port") else nearest_port.get(destination)

    if not src_port or not dst_port:
        return None
    if src_port == dst_port:
        return None  # No sea route if both ends use the same port

    # Get sea distance
    sea_dist = _get_distance(src_port, dst_port, sea_distances)
    if not sea_dist:
        return None

    segments = []
    total_dist = 0

    # First-mile road to port
    if src_port != source:
        first_mile = _get_distance(source, src_port, road_distances)
        if not first_mile:
            return None
        segments.append({"mode": "road", "from": source, "to": src_port, "distance_km": first_mile})
        total_dist += first_mile

    # Sea segment
    segments.append({"mode": "sea", "from": src_port, "to": dst_port, "distance_km": sea_dist})
    total_dist += sea_dist

    # Last-mile road from port
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
    }


def _get_distance(city_a: str, city_b: str, distance_table: dict) -> float | None:
    """
    Look up distance between two cities in a distance table.
    Tries both key orderings (a_b and b_a).
    """
    key1 = f"{city_a}_{city_b}"
    key2 = f"{city_b}_{city_a}"
    return distance_table.get(key1) or distance_table.get(key2)
