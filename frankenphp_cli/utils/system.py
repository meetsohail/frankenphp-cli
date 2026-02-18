"""System command execution with safety and dry-run support."""

import subprocess
from typing import List, Optional

from frankenphp_cli.utils.logger import get_logger

logger = get_logger(__name__)


def run_cmd(
    cmd: List[str],
    *,
    check: bool = True,
    capture: bool = False,
    dry_run: bool = False,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    """
    Run a command via subprocess.run with list args (no shell).
    If dry_run, log and return a fake success result without running.
    """
    if dry_run:
        logger.info("[DRY-RUN] Would run: %s", " ".join(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    logger.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
        cwd=cwd,
        env=env,
    )
    return result


def run_cmd_allow_failure(cmd: List[str], dry_run: bool = False) -> bool:
    """Run command; return True on success, False on failure. Never raises."""
    try:
        run_cmd(cmd, check=True, dry_run=dry_run)
        return True
    except subprocess.CalledProcessError as e:
        logger.warning("Command failed (exit %s): %s", e.returncode, " ".join(cmd))
        return False
