"""PHP version helpers (FrankenPHP uses embedded PHP; no PHP-FPM)."""

from frankenphp_cli.config import DEFAULT_PHP_VERSION
from frankenphp_cli.utils.logger import get_logger

logger = get_logger(__name__)


def normalize_php_version(version: str | None = None) -> str:
    """Return normalized PHP version string (e.g. 8.3). Used for docs/state only."""
    return (version or DEFAULT_PHP_VERSION).strip()
