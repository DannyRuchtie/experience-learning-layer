"""Tests for application configuration."""

from __future__ import annotations

from ell.config import AppConfig, DatabaseConfig


def test_database_config_defaults() -> None:
    """DatabaseConfig should have sensible defaults."""
    db = DatabaseConfig()
    assert db.url == "postgresql://ell:ell@localhost:5432/ell"


def test_app_config_defaults() -> None:
    """AppConfig should have default database config."""
    app = AppConfig()
    assert isinstance(app.database, DatabaseConfig)
    assert app.database.url == "postgresql://ell:ell@localhost:5432/ell"
