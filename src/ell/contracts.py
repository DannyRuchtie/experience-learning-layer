"""Versioned, storage-neutral contracts shared by the benchmark and ELL-Core."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "ell.v0.6"


class Contract(BaseModel):
    """Immutable strict boundary object."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = Field(default=SCHEMA_VERSION, pattern=r"^ell\.v0\.6$")


class Sensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    RESTRICTED = "restricted"


class EvidenceRelation(str, Enum):
    DERIVED_FROM = "derived_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    QUALIFIES = "qualifies"


class LifecycleState(str, Enum):
    PROPOSED = "proposed"
    CORROBORATED = "corroborated"
    CONTESTED = "contested"
    REVISED = "revised"
    SUPERSEDED = "superseded"
    RETIRED = "retired"
    DELETED = "deleted"


class ReviewState(str, Enum):
    QUARANTINED = "quarantined"
    VALIDATED = "validated"
    REJECTED = "rejected"
    COMMITTED = "committed"


class PermissionGrant(Contract):
    principal_id: str = Field(min_length=1)
    purposes: List[str] = Field(min_length=1)


class SourceSpan(Contract):
    span_id: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str

    @model_validator(mode="after")
    def ordered(self) -> "SourceSpan":
        if self.end <= self.start:
            raise ValueError("span end must be greater than start")
        return self


class EvidenceRef(Contract):
    source_id: str = Field(min_length=1)
    span_id: str = Field(min_length=1)


class CostTrace(Contract):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    embedding_tokens: int = Field(default=0, ge=0)
    model_calls: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    hardware_seconds: float = Field(default=0.0, ge=0.0)
    storage_bytes: int = Field(default=0, ge=0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.embedding_tokens


class SourceArtifact(Contract):
    source_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    content: str
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    spans: List[SourceSpan]
    event_time: datetime
    observed_time: datetime
    consent: bool = True
    sensitivity: Sensitivity = Sensitivity.PRIVATE
    grants: List[PermissionGrant] = Field(min_length=1)
    tombstoned: bool = False

    @model_validator(mode="after")
    def spans_match(self) -> "SourceArtifact":
        if self.observed_time < self.event_time:
            raise ValueError("source observed time precedes event time")
        if self.tombstoned:
            if self.content or self.spans:
                raise ValueError("tombstoned sources retain no content or spans")
            return self
        if not self.spans:
            raise ValueError("active sources require at least one span")
        seen = set()
        for span in self.spans:
            if span.span_id in seen:
                raise ValueError("source span identifiers must be unique")
            seen.add(span.span_id)
            if span.end > len(self.content) or self.content[span.start : span.end] != span.text:
                raise ValueError("source span must resolve exactly into content")
        return self


class Episode(Contract):
    episode_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    context: str = Field(min_length=1)
    observation: str = Field(min_length=1)
    action: Optional[str] = None
    outcome: Optional[str] = None
    evidence: List[EvidenceRef] = Field(min_length=1)
    event_time_start: datetime
    event_time_end: datetime
    observed_time: datetime
    sensitivity: Sensitivity = Sensitivity.PRIVATE
    tombstoned: bool = False

    @model_validator(mode="after")
    def ordered(self) -> "Episode":
        if self.event_time_end < self.event_time_start:
            raise ValueError("episode end precedes its start")
        if self.observed_time < self.event_time_end:
            raise ValueError("episode observed time precedes event end")
        return self


class Reflection(Contract):
    reflection_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    reflection_type: str = Field(min_length=1)
    scope: List[str]
    support: List[EvidenceRef]
    counterevidence: List[EvidenceRef]
    uncertainty: float = Field(ge=0.0, le=1.0)
    review_state: ReviewState = ReviewState.QUARANTINED
    generated_by: str = Field(min_length=1)
    observed_time: datetime


class ConceptVersion(Contract):
    concept_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    workspace_id: str = Field(min_length=1)
    proposition: str = Field(min_length=1)
    scope: List[str] = Field(min_length=1)
    conditions: List[str]
    implication: str = Field(min_length=1)
    support: List[EvidenceRef] = Field(min_length=1)
    counterevidence: List[EvidenceRef]
    confidence: float = Field(ge=0.0, le=1.0)
    valid_from: datetime
    valid_to: Optional[datetime] = None
    observed_time: datetime
    lifecycle_state: LifecycleState
    parent_versions: List[str]

    @model_validator(mode="after")
    def validity_ordered(self) -> "ConceptVersion":
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("valid_to must follow valid_from")
        return self

    @property
    def version_id(self) -> str:
        return f"{self.concept_id}:v{self.version}"


class EvidenceLink(Contract):
    link_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    source: EvidenceRef
    target_id: str = Field(min_length=1)
    target_version: Optional[int] = Field(default=None, ge=1)
    relation: EvidenceRelation
    method: str = Field(min_length=1)
    validator: str = Field(min_length=1)
    observed_time: datetime


class ApplicationReceipt(Contract):
    application_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    selected_record_ids: List[str]
    concept_versions: List[str]
    restored_evidence: List[EvidenceRef]
    decision: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    cost: CostTrace
    observed_time: datetime


class Outcome(Contract):
    outcome_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    application_id: str = Field(min_length=1)
    value: float
    observation: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    reliability: float = Field(ge=0.0, le=1.0)
    observed_time: datetime


class AuditEvent(Contract):
    audit_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    prior_version: Optional[str] = None
    new_version: Optional[str] = None
    method: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    observed_time: datetime


class LearningPacket(Contract):
    workspace_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    concept_versions: List[str]
    evidence: List[EvidenceRef]
    conflicts: List[EvidenceRef]
    uncertainty: float = Field(ge=0.0, le=1.0)
    budget_used: int = Field(ge=0)


class InvalidationReport(Contract):
    workspace_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    invalidated_ids: List[str]
    retained_audit_ids: List[str]
    unreachable_projection_ids: List[str]
    complete: bool


class EvaluatorJudgment(Contract):
    judgment_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    evaluator_id: str = Field(min_length=1)
    system_blinded: bool
    success: bool
    unsupported_generalization: bool
    cited_support_ids: List[str]
    material_counterevidence_ids: List[str]
    missed_counterevidence_ids: List[str]
    notes: str = ""


class RunManifest(Contract):
    run_id: str = Field(min_length=1)
    benchmark_version: str = Field(min_length=1)
    partition: str = Field(pattern=r"^(train|development|sealed)$")
    dataset_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    configuration_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    generator_id: str = Field(min_length=1)
    seed_commitment: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    policy_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    logical_started_at: datetime
    cost: CostTrace
    environment: Dict[str, str]


SCHEMA_MODELS = {
    model.__name__: model
    for model in (
        SourceArtifact,
        Episode,
        Reflection,
        ConceptVersion,
        EvidenceLink,
        ApplicationReceipt,
        Outcome,
        AuditEvent,
        RunManifest,
        CostTrace,
        LearningPacket,
        InvalidationReport,
        EvaluatorJudgment,
    )
}
