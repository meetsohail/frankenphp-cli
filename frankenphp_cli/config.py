"""Configuration for frankenphp-cli."""

import os
from pathlib import Path
from typing import Optional

# Paths (configurable via environment)
STATE_DIR = Path(os.environ.get("FRANKENPHP_STATE_DIR", "/var/lib/frankenphp-cli"))
STATE_FILE = STATE_DIR / "state.json"
LOG_FILE = Path(os.environ.get("FRANKENPHP_LOG_FILE", "/var/log/frankenphp-cli.log"))
WEB_ROOT = Path(os.environ.get("FRANKENPHP_WEB_ROOT", "/var/www"))
CADDY_CONFIG_DIR = Path(
    os.environ.get("FRANKENPHP_CADDY_CONFIG_DIR", "/etc/caddy/sites.d")
)
CADDY_RELOAD_CMD = os.environ.get(
    "FRANKENPHP_CADDY_RELOAD", "systemctl reload caddy"
).split()

# Database
DB_HOST = os.environ.get("FRANKENPHP_DB_HOST", "localhost")
DB_ROOT_USER = os.environ.get("FRANKENPHP_DB_ROOT_USER", "root")
DB_ROOT_PASSWORD = os.environ.get("FRANKENPHP_DB_ROOT_PASSWORD", "")

# PHP (FrankenPHP uses embedded PHP; version is for docs/future use only)
DEFAULT_PHP_VERSION = os.environ.get("FRANKENPHP_PHP_VERSION", "8.3")

# WordPress
WP_DOWNLOAD_URL = "https://wordpress.org/latest.tar.gz"
WP_DOWNLOAD_SHA1_URL = "https://wordpress.org/latest.tar.gz.sha1"

# Security
PASSWORD_LENGTH = 32
DOMAIN_REGEX = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"

# Templates (relative to package)
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
CADDY_TEMPLATE = TEMPLATES_DIR / "caddy.tpl"
WP_CONFIG_TEMPLATE = TEMPLATES_DIR / "wp-config.tpl"
