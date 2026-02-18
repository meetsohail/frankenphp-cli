"""WordPress download, extract, and wp-config generation."""

import tarfile
import tempfile
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

from frankenphp_cli.config import WP_CONFIG_TEMPLATE, WP_DOWNLOAD_URL
from frankenphp_cli.utils.logger import get_logger
from frankenphp_cli.utils.system import run_cmd

logger = get_logger(__name__)


def render_wp_config(
    db_name: str,
    db_user: str,
    db_pass: str,
    db_host: str = "localhost",
) -> str:
    """Generate wp-config.php content from template."""
    if WP_CONFIG_TEMPLATE.exists():
        content = WP_CONFIG_TEMPLATE.read_text(encoding="utf-8")
    else:
        content = """<?php
define('DB_NAME', '{db_name}');
define('DB_USER', '{db_user}');
define('DB_PASSWORD', '{db_pass}');
define('DB_HOST', '{db_host}');
"""
    return content.replace("{db_name}", db_name).replace("{db_user}", db_user).replace(
        "{db_pass}", db_pass
    ).replace("{db_host}", db_host)


def download_wordpress(dest_dir: Path, dry_run: bool = False) -> None:
    """Download latest WordPress and extract into dest_dir."""
    if dry_run:
        logger.info("[DRY-RUN] Would download WordPress to %s", dest_dir)
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        logger.info("Downloading WordPress from %s", WP_DOWNLOAD_URL)
        with urlopen(WP_DOWNLOAD_URL, timeout=60) as resp:
            tmp_path.write_bytes(resp.read())
        with tarfile.open(tmp_path, "r:gz") as tar:
            tar.extractall(dest_dir.parent)
        # WordPress extracts as wordpress/ so move contents up if we're targeting site root
        wp_dir = dest_dir.parent / "wordpress"
        if wp_dir.exists():
            for p in wp_dir.iterdir():
                run_cmd(["mv", str(p), str(dest_dir)], dry_run=False)
            wp_dir.rmdir()
        logger.info("WordPress extracted to %s", dest_dir)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def install_wordpress(
    site_root: Path,
    db_name: str,
    db_user: str,
    db_pass: str,
    db_host: str = "localhost",
    dry_run: bool = False,
) -> None:
    """
    Download WordPress, extract to site_root, and write wp-config.php.
    """
    download_wordpress(site_root, dry_run=dry_run)
    config_path = site_root / "wp-config.php"
    config_content = render_wp_config(db_name, db_user, db_pass, db_host)
    if dry_run:
        logger.info("[DRY-RUN] Would write wp-config.php to %s", config_path)
        return
    config_path.write_text(config_content, encoding="utf-8")
    # Safe permissions: dirs 755, files 644
    run_cmd(["find", str(site_root), "-type", "d", "-exec", "chmod", "755", "{}", ";"], dry_run=False)
    run_cmd(["find", str(site_root), "-type", "f", "-exec", "chmod", "644", "{}", ";"], dry_run=False)
    logger.info("WordPress installed at %s", site_root)
