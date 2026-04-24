"""
AI Service — integrates with Google Gemini API to generate route explanations.

This service is the ONLY place where external AI API calls happen.
The AI does NOT perform any calculations — it only explains pre-computed results.
"""

import os
from google import genai

import config


def generate_explanation(route_data: dict) -> str:
    """
    Generate a professional AI explanation for the recommended route.

    Args:
        route_data: dict containing:
            - source, destination, weight, priority
            - ranked_routes: list of all scored routes
            - best_route: the top-ranked route

    Returns:
        A concise, professional explanation string.
        Falls back to a templated explanation if the API is unavailable.
    """
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return _fallback_explanation(route_data)

    prompt = _build_prompt(route_data)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[AI Service] Gemini API error: {e}")
        return _fallback_explanation(route_data)


def _build_prompt(route_data: dict) -> str:
    """
    Construct a structured prompt for Gemini.
    The prompt provides all pre-computed data and asks only for explanation.
    """
    best = route_data["best_route"]
    all_routes = route_data["ranked_routes"]
    priority = route_data["priority"]

    # Build comparison table
    route_summaries = []
    for r in all_routes:
        route_summaries.append(
            f"  - {r['route']['name']} (Rank #{r['rank']}): "
            f"Cost ₹{r['cost']['total_cost']:,.2f}, "
            f"Time {r['time']['total_hours']:.1f}h ({r['time']['total_days']}d), "
            f"Score {r['score']:.4f}"
        )
    comparison = "\n".join(route_summaries)

    # Build segment detail for best route
    segments_desc = []
    for seg in best["route"]["segments"]:
        segments_desc.append(f"    {seg['from']} → {seg['to']} via {seg['mode']} ({seg['distance_km']} km)")
    segments_text = "\n".join(segments_desc)

    # Determine user priority description
    if priority > 0.7:
        priority_desc = "strongly time-sensitive"
    elif priority > 0.5:
        priority_desc = "slightly time-favoring"
    elif priority > 0.3:
        priority_desc = "balanced"
    else:
        priority_desc = "strongly cost-sensitive"

    prompt = f"""You are a logistics advisor. Analyze the following pre-computed route optimization results and provide a concise, professional explanation.

SHIPMENT DETAILS:
- From: {route_data['source']} → To: {route_data['destination']}
- Weight: {route_data['weight']} kg
- User Priority: {priority} ({priority_desc}) — 0 = cost-first, 1 = time-first

ROUTE COMPARISON:
{comparison}

RECOMMENDED ROUTE: {best['route']['name']} (Rank #1)
- Total Cost: ₹{best['cost']['total_cost']:,.2f}
- Total Time: {best['time']['total_hours']:.1f} hours ({best['time']['total_days']} days)
- Score: {best['score']:.4f}
- Segments:
{segments_text}

SCORING WEIGHTS:
- Cost weight: {best['weights']['cost_weight']}
- Time weight: {best['weights']['time_weight']}

INSTRUCTIONS:
1. Explain WHY this route was selected as optimal, referencing the scoring
2. Compare it briefly against alternatives (cost vs time trade-offs)
3. Mention any relevant considerations (multi-modal transfers, delays)
4. Keep it under 150 words, professional tone
5. Do NOT recalculate or modify any numbers — only explain the given data"""

    return prompt


def _fallback_explanation(route_data: dict) -> str:
    """
    Generate a templated explanation when Gemini API is unavailable.
    """
    best = route_data["best_route"]
    priority = route_data["priority"]

    priority_label = "time optimization" if priority > 0.5 else "cost optimization"
    mode_desc = best["route"]["name"]

    return (
        f"Based on your preference for {priority_label} (priority={priority}), "
        f"the '{mode_desc}' route is recommended for shipping {route_data['weight']} kg "
        f"from {route_data['source'].title()} to {route_data['destination'].title()}. "
        f"This route costs ₹{best['cost']['total_cost']:,.2f} and takes approximately "
        f"{best['time']['total_hours']:.1f} hours ({best['time']['total_days']} days). "
        f"It achieved a weighted score of {best['score']:.4f}, making it the optimal "
        f"choice among {len(route_data['ranked_routes'])} evaluated options."
    )
