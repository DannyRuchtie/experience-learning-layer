"""Schemas for reflection generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ReflectionData(BaseModel):
    """A candidate reflection derived from evidence clusters."""
    id: UUID = Field(default_factory=uuid4)
    statement: str
    type: str
    scope: Literal["MOMENTARY", "SESSION", "PROJECT", "ONGOING", "UNKNOWN"] = "ONGOING"
    evidence_ids: list[UUID] = Field(default_factory=list)
    contradiction_ids: list[UUID] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    status: Literal["candidate", "verified", "rejected", "superseded"] = "candidate"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    limitations: list[str] = Field(default_factory=list)
    alternative_interpretations: list[str] = Field(default_factory=list)
