import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_health():
    print("Testing /health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_cities():
    print("\nTesting /cities...")
    try:
        response = requests.get(f"{BASE_URL}/cities")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Found {len(data.get('cities', []))} cities.")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_disruptions():
    print("\nTesting /disruptions...")
    try:
        response = requests.get(f"{BASE_URL}/disruptions")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Found {data.get('count', 0)} active disruptions.")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_route_optimization():
    print("\nTesting /routes (Optimization)...")
    payload = {
        "source": "Pune",
        "destination": "Chennai",
        "weight": 1000,
        "priority": 0.7
    }
    print(f"Payload: {payload}")
    try:
        response = requests.post(f"{BASE_URL}/routes", json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Best Route: {data.get('best_route', {}).get('name')}")
            print(f"AI Insight: {data.get('ai_insight')[:100]}...")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Smart Supply Chain API Tester ===\n")
    
    # 1. Health check
    if not test_health():
        print("!! Server seems to be offline. Make sure to run 'python run.py' first.")
    else:
        # 2. List Cities
        test_cities()
        
        # 3. List Disruptions
        test_disruptions()
        
        # 4. Route Optimization
        test_route_optimization()

    print("\n=== Testing Complete ===")
