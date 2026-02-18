"""Caddy configuration management for FrankenPHP."""

from pathlib import Path
from typing import List

from frankenphp_cli.config import CADDY_CONFIG_DIR, CADDY_RELOAD_CMD, CADDY_TEMPLATE
from frankenphp_cli.utils.logger import get_logger
from frankenphp_cli.utils.system import run_cmd

logger = get_logger(__name__)


def get_site_config_path(primary_domain: str) -> Path:
    """Path to the Caddy site config file for this domain."""
    safe_name = primary_domain.replace(".", "_")
    return CADDY_CONFIG_DIR / f"{safe_name}.conf"


def render_caddy_config(
    primary_domain: str,
    aliases: List[str],
    web_root: Path,
    php_version: str = "8.3",
) -> str:
    """Generate FrankenPHP Caddy config block (php_server, no PHP-FPM)."""
    all_domains = [primary_domain] + [a for a in aliases if a != primary_domain]
    domains_line = " ".join(all_domains)
    if not CADDY_TEMPLATE.exists():
        return f"""{domains_line} {{
    root * {web_root}
    php_server
}}
"""
    content = CADDY_TEMPLATE.read_text(encoding="utf-8")
    return content.replace("{domains_line}", domains_line).replace(
        "{web_root}", str(web_root)
    )


def write_site_config(
    primary_domain: str,
    aliases: List[str],
    web_root: Path,
    php_version: str = "8.3",
    dry_run: bool = False,
) -> None:
    """Write FrankenPHP Caddy config for the site and reload Caddy."""
    path = get_site_config_path(primary_domain)
    config = render_caddy_config(primary_domain, aliases, web_root, php_version)
    if dry_run:
        logger.info("[DRY-RUN] Would write Caddy config to %s", path)
        return
    CADDY_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(config, encoding="utf-8")
    logger.info("Wrote Caddy config: %s", path)
    run_cmd(CADDY_RELOAD_CMD, dry_run=dry_run)


def remove_site_config(primary_domain: str, dry_run: bool = False) -> bool:
    """Remove Caddy config file for the site and reload. Returns True if file existed."""
    path = get_site_config_path(primary_domain)
    if dry_run:
        if path.exists():
            logger.info("[DRY-RUN] Would remove %s and reload Caddy", path)
        return path.exists()
    if not path.exists():
        return False
    path.unlink()
    logger.info("Removed Caddy config: %s", path)
    run_cmd(CADDY_RELOAD_CMD, dry_run=False)
    return True


def reload_caddy(dry_run: bool = False) -> None:
    """Reload Caddy service."""
    run_cmd(CADDY_RELOAD_CMD, dry_run=dry_run)
