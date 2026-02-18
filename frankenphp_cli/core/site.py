"""Site add/delete/list/info with rollback on failure."""

from pathlib import Path
from typing import Any, List, Optional

from frankenphp_cli.config import WEB_ROOT
from frankenphp_cli.core import caddy, database, user as user_core, wordpress
from frankenphp_cli.utils.logger import get_logger
from frankenphp_cli.utils.state import (
    get_site_state,
    load_state,
    remove_site_state,
    save_state,
    set_site_state,
)
from frankenphp_cli.utils.validators import validate_domains

logger = get_logger(__name__)


def _site_path(primary_domain: str) -> Path:
    return WEB_ROOT / primary_domain


def _db_name_from_domain(primary_domain: str) -> str:
    """Generate safe DB name from domain (replace dots with underscores)."""
    return primary_domain.replace(".", "_")[:64]


def add_site(
    primary_domain: str,
    aliases: Optional[List[str]] = None,
    *,
    app: Optional[str] = None,
    php_version: Optional[str] = None,
    create_user: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Add a site: create dir, optional user, DB, optional WordPress, Caddy config, state.
    Returns site info dict. Raises on failure; attempts rollback on error.
    """
    aliases = aliases or []
    ok, err = validate_domains(primary_domain, aliases)
    if not ok:
        raise ValueError(err)

    site_root = _site_path(primary_domain)
    state = load_state()
    existing = get_site_state(state, primary_domain)

    if existing and not force:
        raise ValueError(f"Site already exists: {primary_domain}. Use --force to replace.")

    steps_done: List[tuple[str, Any]] = []  # (step_name, data for rollback)

    def rollback() -> None:
        for step_name, data in reversed(steps_done):
            try:
                if step_name == "state":
                    pass  # state not saved yet on failure
                elif step_name == "caddy":
                    caddy.remove_site_config(primary_domain, dry_run=dry_run)
                elif step_name == "wordpress":
                    pass  # dir will be removed with site_root
                elif step_name == "database":
                    database.delete_database(
                        data["db_name"], db_user=data["db_user"], dry_run=dry_run
                    )
                elif step_name == "user":
                    user_core.delete_linux_user(data["username"], dry_run=dry_run)
                elif step_name == "directory":
                    if site_root.exists():
                        import shutil
                        shutil.rmtree(site_root)
            except Exception as e:
                logger.warning("Rollback step %s failed: %s", step_name, e)

    try:
        # 1. Create directory
        if not dry_run:
            site_root.mkdir(parents=True, exist_ok=force)
        steps_done.append(("directory", {"path": str(site_root)}))

        linux_user: Optional[str] = None
        if create_user:
            uname = primary_domain.split(".")[0][:32]
            user_core.create_linux_user(uname, home_dir=site_root, dry_run=dry_run)
            steps_done.append(("user", {"username": uname}))
            linux_user = uname

        # 2. Database
        db_name = _db_name_from_domain(primary_domain)
        db_user_val: Optional[str] = None
        db_pass_val: Optional[str] = None
        if app == "wordpress" or not existing:
            db_name, db_user_val, db_pass_val = database.create_database(
                db_name, dry_run=dry_run
            )
            steps_done.append(
                ("database", {"db_name": db_name, "db_user": db_user_val or db_name})
            )

        # 3. WordPress if requested
        if app == "wordpress":
            if not db_user_val or not db_pass_val:
                db_name, db_user_val, db_pass_val = database.create_database(
                    db_name, dry_run=dry_run
                )
            wordpress.install_wordpress(
                site_root,
                db_name=db_name,
                db_user=db_user_val,
                db_pass=db_pass_val,
                dry_run=dry_run,
            )
            steps_done.append(("wordpress", {}))

        # 4. Caddy config
        all_aliases = [a for a in aliases if a != primary_domain]
        php_ver = (php_version or "8.3").strip()
        caddy.write_site_config(
            primary_domain, all_aliases, site_root, php_version=php_ver, dry_run=dry_run
        )
        steps_done.append(("caddy", {}))

        # 5. State
        site_data: dict[str, Any] = {
            "primary_domain": primary_domain,
            "aliases": all_aliases,
            "path": str(site_root),
            "php_version": php_version or "8.3",
            "app": app,
        }
        if db_user_val:
            site_data["db_name"] = db_name
            site_data["db_user"] = db_user_val
            site_data["db_password"] = db_pass_val
        if linux_user:
            site_data["linux_user"] = linux_user
        set_site_state(state, primary_domain, site_data)
        if not dry_run:
            save_state(state)
        steps_done.append(("state", {}))

        return site_data
    except Exception as e:
        logger.exception("Site add failed: %s", e)
        if not dry_run:
            rollback()
        raise


def delete_site(primary_domain: str, dry_run: bool = False) -> None:
    """Remove site: dir, DB, Caddy config, state."""
    state = load_state()
    site_data = get_site_state(state, primary_domain)
    site_root = _site_path(primary_domain)

    if not dry_run and site_root.exists():
        import shutil
        shutil.rmtree(site_root)
        logger.info("Removed site directory: %s", site_root)

    if site_data:
        db_name = site_data.get("db_name")
        db_user = site_data.get("db_user")
        if db_name:
            database.delete_database(db_name, db_user=db_user, dry_run=dry_run)

    caddy.remove_site_config(primary_domain, dry_run=dry_run)
    remove_site_state(state, primary_domain)
    if not dry_run:
        save_state(state)
    logger.info("Site deleted: %s", primary_domain)


def list_sites() -> List[dict[str, Any]]:
    """Return list of site info dicts from state."""
    state = load_state()
    sites = state.get("sites", {})
    return [
        {"primary_domain": domain, **data}
        for domain, data in sorted(sites.items())
    ]


def site_info(primary_domain: str) -> Optional[dict[str, Any]]:
    """Return site info for primary domain or None."""
    state = load_state()
    data = get_site_state(state, primary_domain)
    if not data:
        return None
    return {"primary_domain": primary_domain, **data}
