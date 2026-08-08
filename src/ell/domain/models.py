"""Canonical provider-neutral records for the learning kernel."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class FrozenModel(BaseModel):
    """Immutable boundary model so committed records cannot be edited in place."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class MemoryType(str, enum.Enum):
    """Durable memory layers with distinct lifecycle semantics."""

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PREFERENCE = "preference"
    PROCEDURAL = "procedural"
    PROSPECTIVE = "prospective"
    RELATIONAL = "relational"
    REFLECTIVE = "reflective"


class Authority(str, enum.Enum):
    """Ordered source authority; explicit user evidence is strongest."""

    MODEL_INFERRED = "model_inferred"
    SOURCE_ASSERTED = "source_asserted"
    USER_CONFIRMED = "user_confirmed"
    USER_EXPLICIT = "user_explicit"


AUTHORITY_WEIGHT: dict[Authority, float] = {
    Authority.MODEL_INFERRED: 0.55,
    Authority.SOURCE_ASSERTED: 0.7,
    Authority.USER_CONFIRMED: 0.9,
    Authority.USER_EXPLICIT: 1.0,
}


class Sensitivity(str, enum.Enum):
    """Sensitivity classifications used before processing and retrieval."""

    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    RESTRICTED = "restricted"


SENSITIVITY_RANK: dict[Sensitivity, int] = {
    Sensitivity.PUBLIC: 0,
    Sensitivity.INTERNAL: 1,
    Sensitivity.PRIVATE: 2,
    Sensitivity.RESTRICTED: 3,
}


class SourceKind(str, enum.Enum):
    """Kinds of immutable captured artifacts."""

    CONVERSATION = "conversation"
    DOCUMENT = "document"
    AUDIO = "audio"
    EVENT = "event"
    TOOL_RESULT = "tool_result"
    MANUAL = "manual"


class EventType(str, enum.Enum):
    """Normalized event-stream vocabulary independent of source providers."""

    USER_MESSAGE = "user_message"
    ASSISTANT_MESSAGE = "assistant_message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FILE_CHANGE = "file_change"
    DECISION = "decision"
    FEEDBACK = "feedback"
    EXTERNAL_EVENT = "external_event"


class EvidenceRelation(str, enum.Enum):
    """How a source span bears on a claim."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"


class CandidateState(str, enum.Enum):
    """Candidate quarantine lifecycle."""

    PROPOSED = "proposed"
    VALIDATED = "validated"
    AUTO_COMMITTED = "auto_committed"
    AWAITING_REVIEW = "awaiting_review"
    REJECTED = "rejected"
    MERGED = "merged"


class MemoryStatus(str, enum.Enum):
    """Canonical memory lifecycle states."""

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    FORGOTTEN = "forgotten"


class SourceSpan(FrozenModel):
    """Stable, addressable span within a source artifact."""

    id: UUID = Field(default_factory=uuid4)
    text: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def end_follows_start(self) -> SourceSpan:
        """Reject inverted or empty offsets."""
        if self.end <= self.start:
            raise ValueError("span end must be greater than start")
        return self


class SourceArtifact(FrozenModel):
    """Immutable source metadata and normalized text."""

    id: UUID = Field(default_factory=uuid4)
    schema_version: int = Field(default=1, ge=1)
    workspace_id: UUID
    kind: SourceKind
    connector: str = Field(min_length=1)
    external_ref: Optional[str] = None
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    normalized_text: str
    spans: tuple[SourceSpan, ...] = ()
    authors: tuple[UUID, ...] = ()
    observed_at: datetime
    captured_at: datetime = Field(default_factory=utc_now)
    sensitivity: Sensitivity = Sensitivity.PRIVATE
    consent_policy_id: Optional[UUID] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def spans_fit_text(self) -> SourceArtifact:
        """Ensure citations cannot address text outside the artifact."""
        seen: set[UUID] = set()
        for span in self.spans:
            if span.id in seen:
                raise ValueError("source span ids must be unique")
            seen.add(span.id)
            if span.end > len(self.normalized_text):
                raise ValueError("source span exceeds normalized text")
            if self.normalized_text[span.start : span.end] != span.text:
                raise ValueError("source span text does not match normalized text")
        return self


class ExperienceEvent(FrozenModel):
    """One normalized input event before grouping into episodes."""

    id: UUID
    schema_version: int = Field(default=1, ge=1)
    workspace_id: UUID
    source_id: UUID
    source_event_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    parent_id: Optional[UUID] = None
    event_type: EventType
    actor_id: str = Field(min_length=1)
    occurred_at: datetime
    payload: dict[str, Any]
    sensitivity: Sensitivity = Sensitivity.PRIVATE


class Episode(FrozenModel):
    """Bounded experience assembled from one or more normalized events."""

    id: UUID
    schema_version: int = Field(default=1, ge=1)
    workspace_id: UUID
    event_ids: tuple[UUID, ...] = Field(min_length=1)
    timestamp_start: datetime
    timestamp_end: datetime
    actor_id: str = Field(min_length=1)
    participant_ids: tuple[UUID, ...] = ()
    input: Optional[str] = None
    response: Optional[str] = None
    actions: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()
    outcomes: tuple[str, ...] = ()
    entity_ids: tuple[UUID, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def timestamps_are_ordered(self) -> Episode:
        """Reject an episode whose end precedes its beginning."""
        if self.timestamp_end < self.timestamp_start:
            raise ValueError("episode timestamp_end must not precede timestamp_start")
        return self


class EvidenceCitation(FrozenModel):
    """Evidence edge from a derived claim to an exact source span."""

    source_id: UUID
    span_id: UUID
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS


class MemoryValue(FrozenModel):
    """Versionable JSON-compatible object of a memory assertion."""

    type: str = Field(default="text", min_length=1)
    value: str = Field(min_length=1)


class MemoryScope(FrozenModel):
    """Contexts in which a memory is applicable."""

    project_ids: tuple[UUID, ...] = ()
    contexts: tuple[str, ...] = ()


class ProcessorLineage(FrozenModel):
    """Reproducible processor and optional model lineage."""

    processor: str = Field(min_length=1)
    processor_version: str = Field(min_length=1)
    model_provider: Optional[str] = None
    model: Optional[str] = None
    prompt_version: Optional[str] = None


class CandidateMemory(FrozenModel):
    """Quarantined model or deterministic proposal for durable memory."""

    id: UUID = Field(default_factory=uuid4)
    schema_version: int = Field(default=1, ge=1)
    workspace_id: UUID
    memory_type: MemoryType
    subject_id: UUID
    predicate: str = Field(min_length=1)
    object: MemoryValue
    scope: MemoryScope = Field(default_factory=MemoryScope)
    authority: Authority
    confidence: float = Field(ge=0.0, le=1.0)
    salience: float = Field(default=0.5, ge=0.0, le=1.0)
    observed_at: datetime
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    evidence: tuple[EvidenceCitation, ...] = ()
    derived_by: ProcessorLineage
    rationale: str = Field(min_length=1)
    novelty: float = Field(default=1.0, ge=0.0, le=1.0)
    supersedes: tuple[UUID, ...] = ()
    contradicts: tuple[UUID, ...] = ()
    sensitivity: Sensitivity = Sensitivity.PRIVATE
    sensitive_inference: bool = False
    state: CandidateState = CandidateState.PROPOSED

    @model_validator(mode="after")
    def validity_is_ordered(self) -> CandidateMemory:
        """Reject invalid temporal intervals."""
        if self.valid_from and self.valid_to and self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be later than valid_from")
        return self


class MemoryRecord(FrozenModel):
    """Canonical immutable revision of a durable memory."""

    id: UUID = Field(default_factory=uuid4)
    schema_version: int = Field(default=1, ge=1)
    workspace_id: UUID
    memory_type: MemoryType
    subject_id: UUID
    predicate: str
    object: MemoryValue
    scope: MemoryScope
    status: MemoryStatus = MemoryStatus.ACTIVE
    authority: Authority
    confidence: float = Field(ge=0.0, le=1.0)
    salience: float = Field(ge=0.0, le=1.0)
    valid_from: datetime
    valid_to: Optional[datetime] = None
    observed_at: datetime
    committed_at: datetime = Field(default_factory=utc_now)
    evidence: tuple[EvidenceCitation, ...]
    derived_by: ProcessorLineage
    supersedes: tuple[UUID, ...] = ()
    contradicts: tuple[UUID, ...] = ()
    sensitivity: Sensitivity = Sensitivity.PRIVATE
    revision: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def durable_memory_has_authority_or_evidence(self) -> MemoryRecord:
        """Enforce provenance even if a caller bypasses the commit service."""
        if not self.evidence and self.authority is not Authority.USER_EXPLICIT:
            raise ValueError("durable memory requires evidence or explicit user authorship")
        return self


class AuditEvent(FrozenModel):
    """Content-minimized append-only record of a material action."""

    id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    event_type: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    affected_ids: tuple[UUID, ...]
    policy_reason: str
    occurred_at: datetime = Field(default_factory=utc_now)
    trace_id: UUID = Field(default_factory=uuid4)


class RetrievalRequest(FrozenModel):
    """Authorized, budgeted request for memory context."""

    query: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    workspace_id: UUID
    project_ids: tuple[UUID, ...] = ()
    allowed_memory_types: tuple[MemoryType, ...] = tuple(MemoryType)
    maximum_sensitivity: Sensitivity = Sensitivity.PRIVATE
    token_budget: int = Field(default=2400, ge=1)
    include_evidence: bool = True


class RetrievalItem(FrozenModel):
    """A selected memory plus deterministic selection explanation."""

    memory: MemoryRecord
    score: float = Field(ge=0.0)
    why_selected: tuple[str, ...]


class EvidencePacket(FrozenModel):
    """Smallest useful, explainable context returned to a consumer."""

    query_id: UUID = Field(default_factory=uuid4)
    items: tuple[RetrievalItem, ...]
    contradictions: tuple[MemoryRecord, ...]
    estimated_tokens: int = Field(ge=0)
