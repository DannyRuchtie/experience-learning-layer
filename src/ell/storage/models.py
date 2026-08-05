"""Core ORM models for conversations, messages, and evidence."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ell.storage.database import Base


class EvidenceType(str, enum.Enum):
    """Types of evidence that can be extracted from messages."""
    FACT = "FACT"
    PREFERENCE = "PREFERENCE"
    GOAL = "GOAL"
    BELIEF = "BELIEF"
    DECISION = "DECISION"
    CORRECTION = "CORRECTION"
    OUTCOME = "OUTCOME"
    BEHAVIOUR = "BEHAVIOUR"
    RELATIONSHIP = "RELATIONSHIP"
    PROJECT_KNOWLEDGE = "PROJECT_KNOWLEDGE"
    INSTRUCTION = "INSTRUCTION"


class TemporalScope(str, enum.Enum):
    """Temporal scope of evidence."""
    MOMENTARY = "MOMENTARY"
    SESSION = "SESSION"
    PROJECT = "PROJECT"
    ONGOING = "ONGOING"
    UNKNOWN = "UNKNOWN"


class Conversation(Base):
    """A single conversation from an external source."""

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.sequence_number",
    )


class Message(Base):
    """A single message within a conversation."""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    speaker: Mapped[Literal["user", "assistant", "system", "tool"]] = mapped_column(
        Enum("user", "assistant", "system", "tool"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    branch_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    evidence: Mapped[list[Evidence]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )


class Evidence(Base):
    """A meaningful claim extracted from a message."""

    __tablename__ = "evidence"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[EvidenceType] = mapped_column(Enum(EvidenceType), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    temporal_scope: Mapped[TemporalScope] = mapped_column(
        Enum(TemporalScope),
        nullable=False,
    )
    importance: Mapped[float] = mapped_column(Float, nullable=False)
    extraction_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    message: Mapped[Message] = relationship(back_populates="evidence")
    reflections: Mapped[list[Reflection]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
    )


class Reflection(Base):
    """A candidate insight derived from evidence clusters."""

    __tablename__ = "reflections"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_ids: Mapped[list[UUID]] = mapped_column(JSON, nullable=False)
    contradiction_ids: Mapped[list[UUID]] = mapped_column(JSON, nullable=False, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[Literal["candidate", "verified", "rejected", "superseded"]] = mapped_column(
        Enum("candidate", "verified", "rejected", "superseded"),
        nullable=False,
        default="candidate",
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    limitations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    alternative_interpretations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    evidence: Mapped[list[Evidence]] = relationship(
        secondary="reflections_evidence",
        back_populates="reflections",
    )
    concept_versions: Mapped[list[ConceptVersion]] = relationship(
        back_populates="source_reflection",
        cascade="all, delete-orphan",
    )


class ReflectionEvidence(Base):
    """Link table between reflections and evidence."""

    __tablename__ = "reflections_evidence"

    reflection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reflections.id", ondelete="CASCADE"),
        primary_key=True,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Concept(Base):
    """A stable concept with version history."""

    __tablename__ = "concepts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[Literal["active", "weak", "archived"]] = mapped_column(
        Enum("active", "weak", "archived"),
        nullable=False,
        default="active",
    )

    versions: Mapped[list[ConceptVersion]] = relationship(
        back_populates="concept",
        cascade="all, delete-orphan",
        order_by="ConceptVersion.version",
    )


class ConceptOperation(str, enum.Enum):
    """Lifecycle operations on concepts."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    MERGE = "MERGE"
    SPLIT = "SPLIT"
    WEAKEN = "WEAKEN"
    ARCHIVE = "ARCHIVE"
    REACTIVATE = "REACTIVATE"
    REJECT = "REJECT"


class ConceptVersion(Base):
    """An immutable version of a concept."""

    __tablename__ = "concept_versions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    concept_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    operation: Mapped[ConceptOperation] = mapped_column(
        Enum(ConceptOperation),
        nullable=False,
    )
    supporting_evidence_ids: Mapped[list[UUID]] = mapped_column(JSON, nullable=False)
    contradicting_evidence_ids: Mapped[list[UUID]] = mapped_column(
        JSON, nullable=False, default=list,
    )
    source_reflection_ids: Mapped[list[UUID]] = mapped_column(JSON, nullable=False, default=list)

    concept: Mapped[Concept] = relationship(back_populates="versions")
    source_reflection: Mapped[Reflection] = relationship(back_populates="concept_versions")
