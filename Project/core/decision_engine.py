"""
Decision Engine — selects the optimal route using weighted scoring.

Scoring formula:
  score = w_cost × normalized_cost + w_time × normalized_time

Where:
  w_cost = 1 - priority
  w_time = priority
  (priority = 0 → fully cost-optimized, priority = 1 → fully time-optimized)

Lower score = better route.

All logic is pure computation — no external API calls.
"""


def select_best_route(route_analyses: list, priority: float) -> dict:
    """
    Select the best route from a list of analyzed route options.

    Args:
        route_analyses: list of dicts, each containing:
            - route: the route definition
            - cost: cost calculation result from cost_engine
            - time: time calculation result from time_engine
        priority: float 0-1, where 0 = cost-first, 1 = time-first

    Returns:
        The best route analysis dict with added 'score' and 'rank' fields
    """
    if not route_analyses:
        return None

    # Extract raw cost and time values
    costs = [ra["cost"]["total_cost"] for ra in route_analyses]
    times = [ra["time"]["total_hours"] for ra in route_analyses]

    # Normalize to 0-1 scale (min-max normalization)
    norm_costs = _normalize(costs)
    norm_times = _normalize(times)

    # Calculate weighted score for each route
    w_cost = 1.0 - priority
    w_time = priority

    scored_routes = []
    for i, ra in enumerate(route_analyses):
        score = w_cost * norm_costs[i] + w_time * norm_times[i]
        scored_route = {
            **ra,
            "score": round(score, 4),
            "normalized_cost": round(norm_costs[i], 4),
            "normalized_time": round(norm_times[i], 4),
            "weights": {"cost_weight": w_cost, "time_weight": w_time},
        }
        scored_routes.append(scored_route)

    # Sort by score (lower is better)
    scored_routes.sort(key=lambda r: r["score"])

    # Assign ranks
    for rank, sr in enumerate(scored_routes, start=1):
        sr["rank"] = rank

    return scored_routes


def _normalize(values: list) -> list:
    """
    Min-max normalize a list of values to the 0-1 range.
    If all values are identical, returns all zeros (no differentiation).
    """
    if not values:
        return []

    min_val = min(values)
    max_val = max(values)
    spread = max_val - min_val

    if spread == 0:
        return [0.0] * len(values)

    return [(v - min_val) / spread for v in values]
