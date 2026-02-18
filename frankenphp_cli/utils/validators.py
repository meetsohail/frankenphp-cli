"""Validation utilities for domains and identifiers."""

import re
from typing import List

from frankenphp_cli.config import DOMAIN_REGEX
from frankenphp_cli.utils.logger import get_logger

logger = get_logger(__name__)

# DB/user names: alphanumeric and underscore
IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,63}$")
DOMAIN_PATTERN = re.compile(DOMAIN_REGEX)


def validate_domain(domain: str) -> bool:
    """Validate a single domain name. Returns True if valid."""
    domain = domain.strip().lower()
    if not domain or len(domain) > 253:
        return False
    return bool(DOMAIN_PATTERN.fullmatch(domain))


def validate_domains(primary: str, aliases: List[str]) -> tuple[bool, str]:
    """
    Validate primary domain and aliases.
    Returns (True, "") if all valid, else (False, error_message).
    """
    if not validate_domain(primary):
        return False, f"Invalid primary domain: {primary}"
    seen = {primary.lower()}
    for alias in aliases:
        if not validate_domain(alias):
            return False, f"Invalid alias: {alias}"
        if alias.lower() in seen:
            return False, f"Duplicate domain: {alias}"
        seen.add(alias.lower())
    return True, ""


def validate_identifier(name: str, kind: str = "identifier") -> bool:
    """Validate database or Linux username (alphanumeric + underscore)."""
    if not name or len(name) > 64:
        return False
    return bool(IDENTIFIER_REGEX.match(name))


def validate_identifier_or_raise(name: str, kind: str = "identifier") -> None:
    """Validate identifier; raise ValueError if invalid."""
    if not validate_identifier(name, kind):
        raise ValueError(f"Invalid {kind}: {name}")
