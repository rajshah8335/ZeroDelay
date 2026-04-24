"""
Data loader utility.
Handles all JSON file loading with error handling and caching.
"""

import json
import os
from functools import lru_cache


def load_json(filepath: str) -> dict:
    """
    Load and parse a JSON file from the given path.
    Raises FileNotFoundError or json.JSONDecodeError on failure.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=16)
def load_json_cached(filepath: str) -> str:
    """
    Cached version of load_json. Returns raw JSON string for cache compatibility.
    Parse the return value with json.loads() at the call site.
    """
    data = load_json(filepath)
    return json.dumps(data)


def load_nodes(nodes_file: str) -> list:
    """Load the nodes (cities) data."""
    data = load_json(nodes_file)
    return data.get("nodes", [])


def load_routes(routes_file: str) -> dict:
    """Load distance tables for all transport modes."""
    return load_json(routes_file)


def load_cost_config(cost_file: str) -> dict:
    """Load cost configuration parameters for each mode."""
    return load_json(cost_file)


def load_disruptions(disruptions_file: str) -> list:
    """Load active disruption records."""
    data = load_json(disruptions_file)
    return data.get("active_disruptions", [])
