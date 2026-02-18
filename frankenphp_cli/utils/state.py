"""JSON state tracking for sites and domains."""

import json
from pathlib import Path
from typing import Any

from frankenphp_cli.config import STATE_DIR, STATE_FILE
from frankenphp_cli.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_STATE: dict[str, Any] = {"sites": {}, "version": 1}


def _ensure_state_dir() -> None:
    """Create state directory if it does not exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> dict[str, Any]:
    """Load state from JSON file. Returns default state if file missing or invalid."""
    _ensure_state_dir()
    if not STATE_FILE.exists():
        return DEFAULT_STATE.copy()
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data.get("sites"), dict):
            data["sites"] = {}
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load state file: %s. Using empty state.", e)
        return DEFAULT_STATE.copy()


def save_state(state: dict[str, Any]) -> None:
    """Write state to JSON file."""
    _ensure_state_dir()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    logger.debug("State saved to %s", STATE_FILE)


def get_site_state(state: dict[str, Any], primary_domain: str) -> dict[str, Any] | None:
    """Return site entry for primary domain or None."""
    return state.get("sites", {}).get(primary_domain)


def set_site_state(
    state: dict[str, Any],
    primary_domain: str,
    site_data: dict[str, Any],
) -> None:
    """Set or update site entry in state."""
    if "sites" not in state:
        state["sites"] = {}
    state["sites"][primary_domain] = site_data


def remove_site_state(state: dict[str, Any], primary_domain: str) -> bool:
    """Remove site entry. Returns True if it existed."""
    sites = state.get("sites", {})
    if primary_domain in sites:
        del sites[primary_domain]
        return True
    return False
