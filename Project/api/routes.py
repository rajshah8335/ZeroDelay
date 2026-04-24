"""
API Routes — defines all Flask endpoints.

This layer ONLY handles HTTP request/response.
All business logic is delegated to the core and services layers.
"""

from flask import Blueprint, request, jsonify

from utils.validators import validate_route_request
from utils.loader import load_nodes, load_routes, load_cost_config
from core.route_engine import generate_routes
from core.cost_engine import calculate_cost
from core.time_engine import calculate_time
from core.decision_engine import select_best_route
from services.ai_service import generate_explanation
from services.disruption_service import get_active_disruptions
from services.maps_service import geocode_city
import config


# Blueprint for modular route registration
api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/routes", methods=["GET", "POST"], strict_slashes=False)
def optimize_routes():
    """
    POST /api/routes

    Accepts shipment details and returns optimized route options
    with AI-generated insights. Supports ANY city worldwide.

    Request body:
        {
            "source": "London",
            "destination": "New York",
            "weight": 1000,
            "priority": 0.7
        }

    Response:
        {
            "routes": [...],
            "best_route": {...},
            "ai_insight": "..."
        }
    """
    # Handle GET requests with usage info
    if request.method == "GET":
        return jsonify({
            "message": "Optimization endpoint is active. Use POST with a JSON body.",
            "sample_payload": {
                "source": "London",
                "destination": "Tokyo",
                "weight": 1000,
                "priority": 0.7
            },
            "notes": "Supports ANY city worldwide. Priority: 0=cost-first, 1=time-first."
        }), 200

    # ---- Step 1: Validate input ----
    data = request.get_json(silent=True)
    cleaned, error = validate_route_request(data)
    if error:
        return jsonify({"error": error}), 400

    source = cleaned["source"]
    destination = cleaned["destination"]
    weight = cleaned["weight"]
    priority = cleaned["priority"]

    # ---- Step 2: Geocode cities ----
    source_coords = geocode_city(source)
    if not source_coords:
        return jsonify({
            "error": f"Could not find location: '{source}'. Try a more specific name (e.g., 'Mumbai, India')."
        }), 400

    dest_coords = geocode_city(destination)
    if not dest_coords:
        return jsonify({
            "error": f"Could not find location: '{destination}'. Try a more specific name (e.g., 'London, UK')."
        }), 400

    # ---- Step 3: Load fallback data & disruptions ----
    try:
        nodes = load_nodes(config.NODES_FILE)
        routes_data = load_routes(config.ROUTES_FILE)
        cost_config = load_cost_config(config.COST_CONFIG_FILE)
        disruptions = get_active_disruptions()
    except FileNotFoundError as e:
        return jsonify({"error": f"Data loading failed: {str(e)}"}), 500

    # ---- Step 4: Generate route options (live API + fallback) ----
    routes = generate_routes(
        source=source,
        destination=destination,
        source_coords=source_coords,
        dest_coords=dest_coords,
        routes_data=routes_data,
        nodes=nodes,
    )

    if not routes:
        return jsonify({
            "error": f"No routes found between {source} and {destination}. "
                     "This may happen if both cities are landlocked with no road connection."
        }), 404

    # ---- Step 5: Calculate cost & time for each route ----
    route_analyses = []
    for route in routes:
        cost_result = calculate_cost(route, weight, cost_config)
        time_result = calculate_time(route, cost_config, disruptions)
        route_analyses.append({
            "route": route,
            "cost": cost_result,
            "time": time_result,
        })

    # ---- Step 6: Select best route via weighted scoring ----
    ranked_routes = select_best_route(route_analyses, priority)
    best_route = ranked_routes[0] if ranked_routes else None

    # ---- Step 7: Generate AI explanation ----
    ai_context = {
        "source": source,
        "destination": destination,
        "weight": weight,
        "priority": priority,
        "ranked_routes": ranked_routes,
        "best_route": best_route,
    }
    ai_insight = generate_explanation(ai_context)

    # ---- Step 8: Build response ----
    response = {
        "request": {
            "source": source,
            "destination": destination,
            "weight_kg": weight,
            "priority": priority,
            "priority_description": _priority_label(priority),
        },
        "geocoded": {
            "source": {
                "coordinates": source_coords,
            },
            "destination": {
                "coordinates": dest_coords,
            },
        },
        "routes": _format_routes(ranked_routes),
        "best_route": _format_best_route(best_route),
        "ai_insight": ai_insight,
        "disruptions_applied": len(disruptions),
    }

    return jsonify(response), 200


@api_bp.route("/geocode", methods=["GET"], strict_slashes=False)
def geocode():
    """
    GET /api/geocode?city=London

    Geocode any city name to lat/lng coordinates.
    Useful for verifying that a city name will work with the optimizer.
    """
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"error": "Query parameter 'city' is required"}), 400

    coords = geocode_city(city)
    if not coords:
        return jsonify({"error": f"Could not find location: '{city}'"}), 404

    return jsonify({
        "city": city,
        "coordinates": coords,
    }), 200


@api_bp.route("/health", methods=["GET"])
def health_check():
    """GET /api/health — simple health check endpoint."""
    from services.maps_service import _ors_client

    return jsonify({
        "status": "healthy",
        "service": "Smart Supply Chain Optimizer",
        "version": "2.0.0",
        "capabilities": {
            "worldwide_routing": True,
            "openrouteservice": _ors_client is not None,
            "searoute": True,
            "air_freight": True,
            "geocoding": True,
            "gemini_ai": bool(config.GEMINI_API_KEY),
        }
    }), 200


@api_bp.route("/cities", methods=["GET"])
def list_cities():
    """GET /api/cities — list pre-configured cities (fallback data)."""
    try:
        nodes = load_nodes(config.NODES_FILE)
        cities = [
            {
                "id": n["id"],
                "name": n["name"],
                "has_rail": n.get("has_rail_terminal", False),
                "has_port": n.get("has_port", False),
            }
            for n in nodes
        ]
        return jsonify({
            "note": "These are pre-configured Indian cities. The optimizer now supports ANY city worldwide via geocoding.",
            "cities": cities,
        }), 200
    except FileNotFoundError:
        return jsonify({"error": "Node data not found"}), 500


@api_bp.route("/disruptions", methods=["GET"])
def list_disruptions():
    """GET /api/disruptions — list all active disruptions."""
    try:
        disruptions = get_active_disruptions()
        return jsonify({"disruptions": disruptions, "count": len(disruptions)}), 200
    except FileNotFoundError:
        return jsonify({"error": "Disruption data not found"}), 500


# ---- Response formatting helpers ----

def _format_routes(ranked_routes: list) -> list:
    """Format ranked routes for the API response."""
    formatted = []
    for r in ranked_routes:
        formatted.append({
            "rank": r["rank"],
            "name": r["route"]["name"],
            "type": r["route"]["type"],
            "segments": r["route"]["segments"],
            "total_distance_km": r["route"]["total_distance_km"],
            "data_source": r["route"].get("data_source", "unknown"),
            "total_cost_inr": r["cost"]["total_cost"],
            "cost_breakdown": r["cost"]["segments"],
            "total_time_hours": r["time"]["total_hours"],
            "total_time_days": r["time"]["total_days"],
            "time_breakdown": r["time"]["segments"],
            "score": r["score"],
            "normalized_cost": r["normalized_cost"],
            "normalized_time": r["normalized_time"],
        })
    return formatted


def _format_best_route(best: dict) -> dict:
    """Format the best route summary for the API response."""
    if not best:
        return {}
    return {
        "name": best["route"]["name"],
        "type": best["route"]["type"],
        "total_cost_inr": best["cost"]["total_cost"],
        "total_time_hours": best["time"]["total_hours"],
        "total_time_days": best["time"]["total_days"],
        "score": best["score"],
        "segments": best["route"]["segments"],
        "data_source": best["route"].get("data_source", "unknown"),
    }


def _priority_label(priority: float) -> str:
    """Convert numeric priority to a human-readable label."""
    if priority >= 0.8:
        return "Strongly time-optimized"
    elif priority >= 0.6:
        return "Time-favoring"
    elif priority >= 0.4:
        return "Balanced"
    elif priority >= 0.2:
        return "Cost-favoring"
    else:
        return "Strongly cost-optimized"
