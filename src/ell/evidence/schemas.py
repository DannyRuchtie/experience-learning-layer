"""Schemas for evidence extraction."""

from __future__ import annotations

from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EvidenceData(BaseModel):
    """A single piece of evidence extracted from a message."""
    id: UUID = Field(default_factory=uuid4)
    message_id: UUID
    type: Literal[
        "FACT", "PREFERENCE", "GOAL", "BELIEF", "DECISION",
        "CORRECTION", "OUTCOME", "BEHAVIOUR", "RELATIONSHIP",
        "PROJECT_KNOWLEDGE", "INSTRUCTION",
    ]
    statement: str
    subject: str
    temporal_scope: Literal["MOMENTARY", "SESSION", "PROJECT", "ONGOING", "UNKNOWN"]
    importance: float = Field(ge=0.0, le=1.0)
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    supporting_excerpt: Optional[str] = None
