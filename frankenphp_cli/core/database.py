"""Database creation and deletion (MySQL/MariaDB)."""

import secrets
import string
from typing import Optional, Tuple

import mysql.connector
from mysql.connector import Error as MySQLError

from frankenphp_cli.config import (
    DB_HOST,
    DB_ROOT_PASSWORD,
    DB_ROOT_USER,
    PASSWORD_LENGTH,
)
from frankenphp_cli.utils.logger import get_logger
from frankenphp_cli.utils.validators import validate_identifier_or_raise

logger = get_logger(__name__)


def _root_connection():
    """Create connection as root for admin operations."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_ROOT_USER,
        password=DB_ROOT_PASSWORD,
        autocommit=True,
    )


def _generate_password() -> str:
    """Generate a strong random password for DB users."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(PASSWORD_LENGTH))


def create_database(
    db_name: str,
    db_user: Optional[str] = None,
    db_password: Optional[str] = None,
    dry_run: bool = False,
) -> Tuple[str, str, str]:
    """
    Create database and optional user with full privileges.
    Returns (db_name, db_user, db_password).
    """
    validate_identifier_or_raise(db_name, "database name")
    db_user = db_user or db_name
    validate_identifier_or_raise(db_user, "database user")
    db_password = db_password or _generate_password()

    if dry_run:
        logger.info("[DRY-RUN] Would create database %s and user %s", db_name, db_user)
        return db_name, db_user, db_password

    try:
        conn = _root_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS `%s`" % db_name.replace("`", "``"))
        cursor.execute(
            "CREATE USER IF NOT EXISTS %s@localhost IDENTIFIED BY %s",
            (db_user, db_password),
        )
        cursor.execute(
            "GRANT ALL PRIVILEGES ON `%s`.* TO %s@localhost"
            % (db_name.replace("`", "``"), "%s"),
            (db_user,),
        )
        cursor.execute("FLUSH PRIVILEGES")
        cursor.close()
        conn.close()
        logger.info("Created database %s and user %s", db_name, db_user)
        return db_name, db_user, db_password
    except MySQLError as e:
        logger.exception("Database creation failed: %s", e)
        raise RuntimeError(f"Database creation failed: {e}") from e


def delete_database(db_name: str, db_user: Optional[str] = None, dry_run: bool = False) -> None:
    """Drop database and optionally the user."""
    validate_identifier_or_raise(db_name, "database name")
    db_user = db_user or db_name

    if dry_run:
        logger.info("[DRY-RUN] Would drop database %s and user %s", db_name, db_user)
        return

    try:
        conn = _root_connection()
        cursor = conn.cursor()
        cursor.execute("DROP DATABASE IF EXISTS `%s`" % db_name.replace("`", "``"))
        cursor.execute("DROP USER IF EXISTS %s@localhost", (db_user,))
        cursor.execute("FLUSH PRIVILEGES")
        cursor.close()
        conn.close()
        logger.info("Deleted database %s and user %s", db_name, db_user)
    except MySQLError as e:
        logger.exception("Database deletion failed: %s", e)
        raise RuntimeError(f"Database deletion failed: {e}") from e


def database_exists(db_name: str) -> bool:
    """Check if a database exists."""
    try:
        conn = _root_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row is not None
    except MySQLError:
        return False
