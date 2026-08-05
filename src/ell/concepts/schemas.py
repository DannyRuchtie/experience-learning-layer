"""Schemas for concept operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ConceptVersionData(BaseModel):
    """An immutable version of a concept."""
    id: UUID = Field(default_factory=uuid4)
    concept_id: UUID
    version: int
    definition: str
    confidence: float = Field(ge=0.0, le=1.0)
    valid_from: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime | None = None
    operation: Literal[
        "CREATE", "UPDATE", "MERGE", "SPLIT",
        "WEAKEN", "ARCHIVE", "REACTIVATE", "REJECT",
    ]
    supporting_evidence_ids: list[UUID] = Field(default_factory=list)
    contradicting_evidence_ids: list[UUID] = Field(default_factory=list)
    source_reflection_ids: list[UUID] = Field(default_factory=list)
