"""frankenphp-cli: Typer entrypoint and subcommands."""

from pathlib import Path
from typing import Annotated, List, Optional

import typer

from frankenphp_cli import __version__
from frankenphp_cli.config import STATE_DIR
from frankenphp_cli.core import database, site, user as user_core, wordpress
from frankenphp_cli.utils.logger import get_logger, setup_logging
from frankenphp_cli.utils.validators import validate_domain, validate_identifier

# Ensure state dir exists for logging when not root
try:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

setup_logging(console=True)
logger = get_logger(__name__)

app = typer.Typer(
    name="franken",
    help="Manage websites on Linux servers running FrankenPHP (Caddy-based).",
    no_args_is_help=True,
)

# Colors (use string for compatibility across Typer versions)
GREEN = "green"
RED = "red"
CYAN = "cyan"
DIM = "white"  # Step prefix; dim not always available


def _success(msg: str) -> None:
    typer.echo(typer.style(msg, fg=GREEN))


def _error(msg: str) -> None:
    typer.echo(typer.style(msg, fg=RED), err=True)


def _info(msg: str) -> None:
    typer.echo(typer.style(msg, fg=CYAN))


def _step(msg: str) -> None:
    typer.echo(typer.style("  → ", fg=DIM) + msg)


@app.callback(invoke_without_command=True)
def main_callback(
    show_version: Annotated[bool, typer.Option("--version", "-V")] = False,
) -> None:
    if show_version:
        typer.echo(f"frankenphp-cli {__version__}")
        raise typer.Exit(0)


# --- Site ---
site_app = typer.Typer(help="Manage sites (add, delete, list, info).")
app.add_typer(site_app, name="site")


@site_app.command("add")
def site_add(
    domains: Annotated[
        List[str],
        typer.Argument(help="Primary domain, then optional aliases (e.g. example.com www.example.com)"),
    ],
    aliases: Annotated[
        Optional[List[str]],
        typer.Option("--aliases", "-a", help="Additional domains (alternative to positional)"),
    ] = None,
    app_type: Annotated[
        Optional[str],
        typer.Option("--app", "-A", help="App to install (e.g. wordpress)"),
    ] = None,
    php: Annotated[
        Optional[str],
        typer.Option("--php", "-p", help="PHP version (default: 8.3)"),
    ] = None,
    create_user: Annotated[
        bool,
        typer.Option("--user", "-u", help="Create a Linux user for this site"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing site"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview commands without executing"),
    ] = False,
) -> None:
    """Add a site with optional aliases and WordPress."""
    if not domains:
        _error("At least one domain is required.")
        raise typer.Exit(1)
    primary_domain = domains[0]
    positional_aliases = domains[1:] if len(domains) > 1 else []
    if aliases is not None:
        all_aliases = list(aliases)
    else:
        all_aliases = positional_aliases
    _info("Adding site: " + primary_domain)
    if not validate_domain(primary_domain):
        _error(f"Invalid primary domain: {primary_domain}")
        raise typer.Exit(1)
    try:
        _step("Creating site directory and config...")
        data = site.add_site(
            primary_domain,
            aliases=all_aliases,
            app=app_type,
            php_version=php,
            create_user=create_user,
            force=force,
            dry_run=dry_run,
        )
        if dry_run:
            _success("[DRY-RUN] Site add completed (no changes made).")
            return
        _success("Site added successfully.")
        typer.echo(f"  Domain: {primary_domain}")
        if data.get("aliases"):
            typer.echo(f"  Aliases: {', '.join(data['aliases'])}")
        typer.echo(f"  Path: {data.get('path', '')}")
        if data.get("db_name"):
            typer.echo(f"  Database: {data['db_name']}")
    except ValueError as e:
        _error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        _error(f"Failed: {e}")
        logger.exception("Site add failed")
        raise typer.Exit(1)


@site_app.command("delete")
def site_delete(
    primary_domain: Annotated[str, typer.Argument(help="Primary domain to remove")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview only")] = False,
) -> None:
    """Delete a site (directory, DB, Caddy config, state)."""
    _info("Deleting site: " + primary_domain)
    try:
        site.delete_site(primary_domain, dry_run=dry_run)
        if dry_run:
            _success("[DRY-RUN] Delete completed (no changes made).")
        else:
            _success("Site deleted.")
    except Exception as e:
        _error(f"Failed: {e}")
        logger.exception("Site delete failed")
        raise typer.Exit(1)


@site_app.command("list")
def site_list_cmd() -> None:
    """List all managed sites."""
    try:
        sites = site.list_sites()
        if not sites:
            typer.echo("No sites found.")
            return
        for s in sites:
            domains = [s["primary_domain"]] + s.get("aliases", [])
            typer.echo(f"  {s['primary_domain']}  {', '.join(s.get('aliases', []))}")
    except Exception as e:
        _error(f"Failed: {e}")
        raise typer.Exit(1)


@site_app.command("info")
def site_info_cmd(
    primary_domain: Annotated[str, typer.Argument(help="Primary domain")],
) -> None:
    """Show details for a site."""
    try:
        data = site.site_info(primary_domain)
        if not data:
            _error(f"Site not found: {primary_domain}")
            raise typer.Exit(1)
        typer.echo(f"Domain:     {data.get('primary_domain')}")
        typer.echo(f"Aliases:    {', '.join(data.get('aliases', []))}")
        typer.echo(f"Path:       {data.get('path', '')}")
        typer.echo(f"PHP:        {data.get('php_version', '')}")
        typer.echo(f"App:        {data.get('app', '')}")
        typer.echo(f"Database:   {data.get('db_name', '')}")
    except typer.Exit:
        raise
    except Exception as e:
        _error(f"Failed: {e}")
        raise typer.Exit(1)


# --- Database ---
db_app = typer.Typer(help="Manage databases.")
app.add_typer(db_app, name="db")


@db_app.command("create")
def db_create(
    name: Annotated[str, typer.Argument(help="Database name")],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Create a database and user with generated password."""
    if not validate_identifier(name):
        _error(f"Invalid database name: {name}")
        raise typer.Exit(1)
    _info("Creating database: " + name)
    try:
        db_name, db_user, db_pass = database.create_database(name, dry_run=dry_run)
        if dry_run:
            _success("[DRY-RUN] Database create completed (no changes made).")
            return
        _success("Database created.")
        typer.echo(f"  Database: {db_name}")
        typer.echo(f"  User:     {db_user}")
        typer.echo(f"  Password: {db_pass}")
    except Exception as e:
        _error(f"Failed: {e}")
        raise typer.Exit(1)


@db_app.command("delete")
def db_delete(
    name: Annotated[str, typer.Argument(help="Database name")],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Delete a database and its user."""
    if not validate_identifier(name):
        _error(f"Invalid database name: {name}")
        raise typer.Exit(1)
    _info("Deleting database: " + name)
    try:
        database.delete_database(name, dry_run=dry_run)
        if dry_run:
            _success("[DRY-RUN] Database delete completed (no changes made).")
        else:
            _success("Database deleted.")
    except Exception as e:
        _error(f"Failed: {e}")
        raise typer.Exit(1)


# --- WordPress ---
wp_app = typer.Typer(help="WordPress management.")
app.add_typer(wp_app, name="wordpress")


@wp_app.command("install")
def wordpress_install(
    primary_domain: Annotated[str, typer.Argument(help="Site primary domain")],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Install WordPress on an existing site."""
    _info("Installing WordPress for: " + primary_domain)
    try:
        info = site.site_info(primary_domain)
        if not info:
            _error(f"Site not found: {primary_domain}. Add the site first.")
            raise typer.Exit(1)
        path = Path(info["path"])
        db_name = info.get("db_name")
        db_user = info.get("db_user")
        db_pass = info.get("db_password")
        if not db_name or not db_user or not db_pass:
            _step("Creating database for WordPress...")
            db_name, db_user, db_pass = database.create_database(
                primary_domain.replace(".", "_")[:64], dry_run=dry_run
            )
            # Update state with new DB
            from frankenphp_cli.utils.state import load_state, save_state, set_site_state
            state = load_state()
            info["db_name"] = db_name
            info["db_user"] = db_user
            info["db_password"] = db_pass
            set_site_state(state, primary_domain, info)
            if not dry_run:
                save_state(state)
        _step("Downloading and extracting WordPress...")
        wordpress.install_wordpress(
            path,
            db_name=db_name,
            db_user=db_user,
            db_pass=db_pass,
            dry_run=dry_run,
        )
        if dry_run:
            _success("[DRY-RUN] WordPress install completed (no changes made).")
        else:
            _success("WordPress installed.")
    except typer.Exit:
        raise
    except Exception as e:
        _error(f"Failed: {e}")
        logger.exception("WordPress install failed")
        raise typer.Exit(1)


# --- User ---
user_app = typer.Typer(help="Linux user management.")
app.add_typer(user_app, name="user")


@user_app.command("create")
def user_create(
    username: Annotated[str, typer.Argument(help="Linux username")],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Create a Linux user."""
    if not validate_identifier(username):
        _error(f"Invalid username: {username}")
        raise typer.Exit(1)
    _info("Creating user: " + username)
    try:
        user_core.create_linux_user(username, dry_run=dry_run)
        if dry_run:
            _success("[DRY-RUN] User create completed (no changes made).")
        else:
            _success("User created.")
    except Exception as e:
        _error(f"Failed: {e}")
        raise typer.Exit(1)


@user_app.command("delete")
def user_delete(
    username: Annotated[str, typer.Argument(help="Linux username")],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Delete a Linux user (and home directory)."""
    if not validate_identifier(username):
        _error(f"Invalid username: {username}")
        raise typer.Exit(1)
    _info("Deleting user: " + username)
    try:
        user_core.delete_linux_user(username, dry_run=dry_run)
        if dry_run:
            _success("[DRY-RUN] User delete completed (no changes made).")
        else:
            _success("User deleted.")
    except Exception as e:
        _error(f"Failed: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
