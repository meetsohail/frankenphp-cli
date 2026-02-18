"""Tests for state load/save."""

from pathlib import Path
from unittest.mock import patch

import pytest

from frankenphp_cli.utils.state import (
    get_site_state,
    load_state,
    remove_site_state,
    save_state,
    set_site_state,
)


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    return tmp_path / "state"


@pytest.fixture
def state_file(state_dir: Path) -> Path:
    return state_dir / "state.json"


def test_load_state_missing_file(state_dir: Path, state_file: Path) -> None:
    with patch("frankenphp_cli.utils.state.STATE_DIR", state_dir), patch(
        "frankenphp_cli.utils.state.STATE_FILE", state_file
    ):
        state = load_state()
        assert state["sites"] == {}
        assert state["version"] == 1


def test_save_and_load_state(state_dir: Path, state_file: Path) -> None:
    with patch("frankenphp_cli.utils.state.STATE_DIR", state_dir), patch(
        "frankenphp_cli.utils.state.STATE_FILE", state_file
    ):
        st = load_state()
        set_site_state(st, "example.com", {"path": "/var/www/example.com"})
        save_state(st)
        loaded = load_state()
        assert get_site_state(loaded, "example.com") == {"path": "/var/www/example.com"}
        remove_site_state(loaded, "example.com")
        assert get_site_state(loaded, "example.com") is None
