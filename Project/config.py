"""
Application configuration module.
Centralizes all configuration constants and API keys.
"""

import os

# Flask settings
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Gemini API configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.1-pro-preview"

# Data file paths (relative to project root)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
NODES_FILE = os.path.join(DATA_DIR, "nodes.json")
ROUTES_FILE = os.path.join(DATA_DIR, "routes.json")
COST_CONFIG_FILE = os.path.join(DATA_DIR, "cost_config.json")
DISRUPTIONS_FILE = os.path.join(DATA_DIR, "disruptions.json")

# Priority weight mapping
# priority = 0.0 → fully cost-optimized
# priority = 1.0 → fully time-optimized
DEFAULT_PRIORITY = 0.5
