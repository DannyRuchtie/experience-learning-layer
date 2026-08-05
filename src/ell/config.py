"""Application configuration loaded from environment."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database connection settings."""
    url: str = Field(
        default="postgresql://ell:ell@localhost:5432/ell",
        description="PostgreSQL connection URL.",
    )


class AppConfig(BaseModel):
    """Top-level application configuration."""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
