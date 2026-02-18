"""Logging setup for frankenphp-cli."""

import logging
import sys
from pathlib import Path
from typing import Optional

from frankenphp_cli.config import LOG_FILE


def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True,
) -> None:
    """Configure logging to file and optionally console."""
    log_path = log_file or LOG_FILE
    handlers: list[logging.Handler] = []
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    except (OSError, PermissionError):
        pass  # Fall back to console only when file is not writable
    if console:
        handlers.append(logging.StreamHandler(sys.stderr))
    if not handlers:
        handlers.append(logging.StreamHandler(sys.stderr))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name."""
    return logging.getLogger(name)
