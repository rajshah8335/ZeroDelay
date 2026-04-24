"""
Application configuration module.
Centralizes all configuration constants and API keys.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask settings
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Gemini API configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# OpenRouteService API configuration (free, 2000 req/day)
# Sign up at https://openrouteservice.org to get your free key
ORS_API_KEY = os.environ.get("ORS_API_KEY", "")

# API timeout in seconds (for external service calls)
API_TIMEOUT = 10

# Geocoding settings
GEOCODER_USER_AGENT = "ZeroDelay-SupplyChain-Optimizer/1.0"

# Data file paths (used as fallback when APIs are unavailable)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
NODES_FILE = os.path.join(DATA_DIR, "nodes.json")
ROUTES_FILE = os.path.join(DATA_DIR, "routes.json")
COST_CONFIG_FILE = os.path.join(DATA_DIR, "cost_config.json")
DISRUPTIONS_FILE = os.path.join(DATA_DIR, "disruptions.json")

# Rail estimation factors (no free global rail API exists)
RAIL_DISTANCE_FACTOR = 1.1   # Rail routes are ~10% longer than road
RAIL_TIME_FACTOR = 0.85      # Rail is ~15% faster than road driving time

# Priority weight mapping
# priority = 0.0 → fully cost-optimized
# priority = 1.0 → fully time-optimized
DEFAULT_PRIORITY = 0.5
