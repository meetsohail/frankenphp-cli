"""Linux user creation and deletion."""

import subprocess
from pathlib import Path
from typing import Optional

from frankenphp_cli.utils.logger import get_logger
from frankenphp_cli.utils.system import run_cmd
from frankenphp_cli.utils.validators import validate_identifier_or_raise

logger = get_logger(__name__)


def create_linux_user(
    username: str,
    home_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> None:
    """Create a Linux user with optional home directory."""
    validate_identifier_or_raise(username, "username")
    home = home_dir or Path(f"/home/{username}")

    if dry_run:
        logger.info("[DRY-RUN] Would create user %s with home %s", username, home)
        return

    # useradd -m -d /home/username username (or custom home)
    cmd = ["useradd", "-m", "-d", str(home), username]
    try:
        run_cmd(cmd, dry_run=False)
        logger.info("Created user %s", username)
    except subprocess.CalledProcessError as e:
        logger.exception("User creation failed: %s", e)
        raise RuntimeError(f"User creation failed: {e}") from e


def delete_linux_user(username: str, remove_home: bool = True, dry_run: bool = False) -> None:
    """Remove a Linux user and optionally home directory."""
    validate_identifier_or_raise(username, "username")

    if dry_run:
        logger.info("[DRY-RUN] Would delete user %s (remove_home=%s)", username, remove_home)
        return

    cmd = ["userdel", "-r" if remove_home else "", username]
    cmd = [c for c in cmd if c]
    try:
        run_cmd(cmd, dry_run=False)
        logger.info("Deleted user %s", username)
    except subprocess.CalledProcessError as e:
        logger.exception("User deletion failed: %s", e)
        raise RuntimeError(f"User deletion failed: {e}") from e


def user_exists(username: str) -> bool:
    """Check if a Linux user exists."""
    try:
        run_cmd(["id", username], check=True, capture=True)
        return True
    except subprocess.CalledProcessError:
        return False


def chown_recursive(path: Path, user: str, group: Optional[str] = None, dry_run: bool = False) -> None:
    """Recursively set ownership. Group defaults to user."""
    own = f"{user}:{group or user}"
    run_cmd(["chown", "-R", own, str(path)], dry_run=dry_run)
