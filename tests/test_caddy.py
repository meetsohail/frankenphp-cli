"""Tests for Caddy config rendering."""

from pathlib import Path

import pytest

from frankenphp_cli.core.caddy import get_site_config_path, render_caddy_config


def test_get_site_config_path() -> None:
    assert "example_com" in str(get_site_config_path("example.com"))
    assert get_site_config_path("example.com").suffix == ".conf"


def test_render_caddy_config() -> None:
    """FrankenPHP uses php_server (embedded PHP), not php_fastcgi."""
    out = render_caddy_config(
        "example.com",
        ["www.example.com"],
        Path("/var/www/example.com"),
        php_version="8.3",
    )
    assert "example.com" in out
    assert "www.example.com" in out
    assert "/var/www/example.com" in out
    assert "php_server" in out
    assert "php_fastcgi" not in out
