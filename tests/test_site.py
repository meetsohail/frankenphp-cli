"""Tests for site validation and state."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from frankenphp_cli.utils.validators import (
    validate_domain,
    validate_domains,
    validate_identifier,
)


class TestValidateDomain:
    """Test domain validation."""

    def test_valid_domain(self) -> None:
        assert validate_domain("example.com") is True
        assert validate_domain("www.example.com") is True
        assert validate_domain("sub.domain.example.com") is True

    def test_invalid_domain(self) -> None:
        assert validate_domain("") is False
        assert validate_domain("invalid") is False
        assert validate_domain(".example.com") is False
        assert validate_domain("example..com") is False


class TestValidateDomains:
    """Test primary + aliases validation."""

    def test_valid_primary_and_aliases(self) -> None:
        ok, err = validate_domains("example.com", ["www.example.com"])
        assert ok is True
        assert err == ""

    def test_invalid_primary(self) -> None:
        ok, err = validate_domains("notadomain", [])
        assert ok is False
        assert "Invalid primary domain" in err

    def test_duplicate_alias(self) -> None:
        ok, err = validate_domains("example.com", ["example.com"])
        assert ok is False
        assert "Duplicate" in err


class TestValidateIdentifier:
    """Test DB/user identifier validation."""

    def test_valid(self) -> None:
        assert validate_identifier("example_db") is True
        assert validate_identifier("user123") is True

    def test_invalid(self) -> None:
        assert validate_identifier("") is False
        assert validate_identifier("123leading") is False
        assert validate_identifier("has-dash") is False
