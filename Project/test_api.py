"""
API Test Script — tests all endpoints including worldwide routing.
Run with: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"


def test_health():
    """Test the health check endpoint."""
    print("=" * 60)
    print("1. Testing /health...")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Service: {data.get('service')}")
        print(f"   Version: {data.get('version')}")
        caps = data.get("capabilities", {})
        print(f"   OpenRouteService: {'✅' if caps.get('openrouteservice') else '❌ (set ORS_API_KEY in .env)'}")
        print(f"   Geocoding: {'✅' if caps.get('geocoding') else '❌'}")
        print(f"   Searoute: {'✅' if caps.get('searoute') else '❌'}")
        print(f"   Air Freight: {'✅' if caps.get('air_freight') else '❌'}")
        print(f"   Gemini AI: {'✅' if caps.get('gemini_ai') else '⚠️ (fallback mode)'}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_cities():
    """Test the cities listing endpoint."""
    print("\n" + "=" * 60)
    print("2. Testing /cities...")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/cities")
        print(f"   Status: {response.status_code}")
        data = response.json()
        cities = data.get("cities", [])
        print(f"   Pre-configured cities: {len(cities)}")
        for c in cities[:5]:
            print(f"     - {c['name']} (rail: {c['has_rail']}, port: {c['has_port']})")
        if len(cities) > 5:
            print(f"     ... and {len(cities) - 5} more")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_disruptions():
    """Test the disruptions listing endpoint."""
    print("\n" + "=" * 60)
    print("3. Testing /disruptions...")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/disruptions")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Active disruptions: {data.get('count', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_geocode(city):
    """Test the geocoding endpoint."""
    print(f"\n   Geocoding '{city}'...")
    try:
        response = requests.get(f"{BASE_URL}/geocode", params={"city": city})
        if response.status_code == 200:
            data = response.json()
            coords = data.get("coordinates", {})
            print(f"   ✅ {city} → ({coords.get('lat')}, {coords.get('lng')})")
            return True
        else:
            print(f"   ❌ Failed: {response.json().get('error')}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_route_optimization(source, destination, weight=1000, priority=0.7, label=""):
    """Test the route optimization endpoint."""
    payload = {
        "source": source,
        "destination": destination,
        "weight": weight,
        "priority": priority,
    }
    print(f"\n   {label or f'{source} → {destination}'} ({weight}kg, priority={priority})")

    try:
        response = requests.post(f"{BASE_URL}/routes", json=payload, timeout=30)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            best = data.get("best_route", {})
            routes = data.get("routes", [])
            print(f"   Routes found: {len(routes)}")
            for r in routes:
                print(f"     #{r['rank']} {r['name']} — ₹{r['total_cost_inr']:,.0f}, "
                      f"{r['total_time_hours']:.1f}h, source: {r.get('data_source', 'N/A')}")
            print(f"   ⭐ Best: {best.get('name')} (₹{best.get('total_cost_inr', 0):,.0f}, "
                  f"{best.get('total_time_hours', 0):.1f}h)")
            ai = data.get("ai_insight", "")
            print(f"   AI: {ai[:120]}..." if len(ai) > 120 else f"   AI: {ai}")
            return True
        else:
            error = response.json().get("error", response.text)
            print(f"   ❌ Error: {error}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n🌍 Smart Supply Chain Optimizer — API Test Suite v2.0\n")

    # 1. Health check
    if not test_health():
        print("\n❌ Server is offline. Run 'python run.py' first.")
        exit(1)

    # 2. List cities
    test_cities()

    # 3. Disruptions
    test_disruptions()

    # 4. Geocoding tests
    print("\n" + "=" * 60)
    print("4. Testing /geocode (worldwide)...")
    print("=" * 60)
    test_geocode("London")
    test_geocode("Tokyo")
    test_geocode("Mumbai")
    test_geocode("New York")

    # 5. Route optimization tests
    print("\n" + "=" * 60)
    print("5. Testing /routes (Route Optimization)...")
    print("=" * 60)

    # India (should work with both live and fallback)
    test_route_optimization("Pune", "Chennai", 1000, 0.7, "🇮🇳 India: Pune → Chennai")

    # Europe (live API only)
    test_route_optimization("Berlin", "Paris", 2000, 0.5, "🇪🇺 Europe: Berlin → Paris")

    # Intercontinental (sea route expected)
    test_route_optimization("Shanghai", "London", 5000, 0.3, "🌏 Intercontinental: Shanghai → London")

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
