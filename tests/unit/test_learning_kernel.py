"""Unit tests for the provider-neutral governed learning kernel."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from ell.domain.models import (
    Authority,
    CandidateMemory,
    CandidateState,
    EvidenceCitation,
    MemoryRecord,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    MemoryValue,
    ProcessorLineage,
    RetrievalRequest,
    Sensitivity,
    SourceArtifact,
    SourceKind,
    SourceSpan,
)
from ell.domain.repositories import (
    ConcurrencyError,
    InMemoryArtifactRepository,
    InMemoryAuditSink,
    InMemoryMemoryRepository,
)
from ell.domain.services import LearningKernel, RetrievalService, ValidationError

NOW = datetime(2026, 8, 8, 10, 0, tzinfo=timezone.utc)


def source_artifact(
    workspace_id: UUID,
    text: str = "For documentation, always use portable Markdown.",
    *,
    sensitivity: Sensitivity = Sensitivity.PRIVATE,
) -> SourceArtifact:
    """Build a valid immutable source with one exact span."""
    span = SourceSpan(text=text, start=0, end=len(text))
    return SourceArtifact(
        workspace_id=workspace_id,
        kind=SourceKind.CONVERSATION,
        connector="test",
        content_hash=f"sha256:{hashlib.sha256(text.encode()).hexdigest()}",
        normalized_text=text,
        spans=(span,),
        observed_at=NOW,
        sensitivity=sensitivity,
    )


def candidate_memory(
    workspace_id: UUID,
    artifact: SourceArtifact | None,
    *,
    authority: Authority = Authority.USER_EXPLICIT,
    value: str = "portable Markdown",
    memory_type: MemoryType = MemoryType.PREFERENCE,
    supersedes: tuple[UUID, ...] = (),
    contradicts: tuple[UUID, ...] = (),
    sensitive_inference: bool = False,
    sensitivity: Sensitivity = Sensitivity.PRIVATE,
    scope: MemoryScope | None = None,
) -> CandidateMemory:
    """Build a candidate with optional exact source evidence."""
    citations = ()
    if artifact is not None:
        citations = (EvidenceCitation(source_id=artifact.id, span_id=artifact.spans[0].id),)
    return CandidateMemory(
        workspace_id=workspace_id,
        memory_type=memory_type,
        subject_id=uuid4(),
        predicate="prefers",
        object=MemoryValue(value=value),
        scope=scope or MemoryScope(contexts=("documentation",)),
        authority=authority,
        confidence=0.98,
        observed_at=NOW,
        evidence=citations,
        derived_by=ProcessorLineage(
            processor="test-extractor",
            processor_version="1.0.0",
        ),
        rationale="The statement directly expresses a scoped preference.",
        supersedes=supersedes,
        contradicts=contradicts,
        sensitive_inference=sensitive_inference,
        sensitivity=sensitivity,
    )


@pytest.fixture
def kernel_parts() -> tuple[
    LearningKernel,
    InMemoryArtifactRepository,
    InMemoryMemoryRepository,
    InMemoryAuditSink,
]:
    """Create isolated in-memory adapters and kernel."""
    artifacts = InMemoryArtifactRepository()
    memories = InMemoryMemoryRepository()
    audit = InMemoryAuditSink()
    return LearningKernel(artifacts, memories, audit), artifacts, memories, audit


def test_source_spans_must_match_normalized_text() -> None:
    """Citation offsets cannot silently point at different content."""
    with pytest.raises(PydanticValidationError, match="does not match"):
        SourceArtifact(
            workspace_id=uuid4(),
            kind=SourceKind.MANUAL,
            connector="test",
            content_hash=f"sha256:{'0' * 64}",
            normalized_text="actual",
            spans=(SourceSpan(text="wrong", start=0, end=5),),
            observed_at=NOW,
        )


def test_memory_record_itself_enforces_provenance() -> None:
    """A storage adapter cannot bypass the no-unsupported-memory invariant."""
    with pytest.raises(PydanticValidationError, match="requires evidence"):
        MemoryRecord(
            workspace_id=uuid4(),
            memory_type=MemoryType.SEMANTIC,
            subject_id=uuid4(),
            predicate="works_at",
            object=MemoryValue(value="Example Corp"),
            scope=MemoryScope(),
            authority=Authority.MODEL_INFERRED,
            confidence=0.9,
            salience=0.5,
            valid_from=NOW,
            observed_at=NOW,
            evidence=(),
            derived_by=ProcessorLineage(
                processor="test-extractor",
                processor_version="1.0.0",
            ),
        )


def test_explicit_candidate_commits_with_evidence_and_audit(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """An explicit, supported preference becomes canonical memory."""
    kernel, _, memories, audit = kernel_parts
    workspace_id = uuid4()
    artifact = source_artifact(workspace_id)
    kernel.capture_source(artifact, idempotency_key="source-1", actor_id="user")

    result = kernel.submit_candidate(
        candidate_memory(workspace_id, artifact),
        idempotency_key="candidate-1",
        actor_id="processor",
    )

    assert isinstance(result, MemoryRecord)
    assert result.evidence[0].span_id == artifact.spans[0].id
    assert result.status is MemoryStatus.ACTIVE
    assert [event.event_type for event in audit.list_events(workspace_id)] == [
        "SourceCaptured",
        "MemoryCommitted",
    ]
    assert memories.list_memories(workspace_id) == (result,)


def test_submit_candidate_is_idempotent(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """A retried mutation returns the first result without another commit event."""
    kernel, _, _, audit = kernel_parts
    workspace_id = uuid4()
    artifact = source_artifact(workspace_id)
    kernel.capture_source(artifact, idempotency_key="source", actor_id="user")
    candidate = candidate_memory(workspace_id, artifact)

    first = kernel.submit_candidate(candidate, idempotency_key="same", actor_id="processor")
    second = kernel.submit_candidate(candidate, idempotency_key="same", actor_id="processor")

    assert second == first
    assert (
        sum(event.event_type == "MemoryCommitted" for event in audit.list_events(workspace_id)) == 1
    )


def test_missing_or_cross_workspace_evidence_is_rejected(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """A candidate cannot cite inaccessible evidence."""
    kernel, _, _, _ = kernel_parts
    source_workspace = uuid4()
    candidate_workspace = uuid4()
    artifact = source_artifact(source_workspace)
    kernel.capture_source(artifact, idempotency_key="source", actor_id="user")

    with pytest.raises(ValidationError, match="another workspace"):
        kernel.submit_candidate(
            candidate_memory(candidate_workspace, artifact),
            idempotency_key="candidate",
            actor_id="processor",
        )


def test_candidate_cannot_lower_source_sensitivity(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """Restricted source policy travels to derived records."""
    kernel, _, _, _ = kernel_parts
    workspace_id = uuid4()
    artifact = source_artifact(workspace_id, sensitivity=Sensitivity.RESTRICTED)
    kernel.capture_source(artifact, idempotency_key="source", actor_id="user")

    with pytest.raises(ValidationError, match="cannot lower"):
        kernel.submit_candidate(
            candidate_memory(
                workspace_id,
                artifact,
                sensitivity=Sensitivity.PRIVATE,
            ),
            idempotency_key="candidate",
            actor_id="processor",
        )


def test_unsupported_and_sensitive_inferred_candidates_are_rejected(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """Policy rejects unsupported learning and sensitive model inference."""
    kernel, _, _, _ = kernel_parts
    workspace_id = uuid4()

    unsupported = kernel.submit_candidate(
        candidate_memory(workspace_id, None, authority=Authority.MODEL_INFERRED),
        idempotency_key="unsupported",
        actor_id="processor",
    )
    assert isinstance(unsupported, CandidateMemory)
    assert unsupported.state is CandidateState.REJECTED

    artifact = source_artifact(workspace_id)
    kernel.capture_source(artifact, idempotency_key="source", actor_id="user")
    sensitive = kernel.submit_candidate(
        candidate_memory(
            workspace_id,
            artifact,
            authority=Authority.MODEL_INFERRED,
            sensitive_inference=True,
        ),
        idempotency_key="sensitive",
        actor_id="processor",
    )
    assert isinstance(sensitive, CandidateMemory)
    assert sensitive.state is CandidateState.REJECTED


def test_non_explicit_candidate_waits_for_review(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """Ordinary inferred learning remains quarantined from retrieval."""
    kernel, _, memories, _ = kernel_parts
    workspace_id = uuid4()
    artifact = source_artifact(workspace_id)
    kernel.capture_source(artifact, idempotency_key="source", actor_id="user")

    result = kernel.submit_candidate(
        candidate_memory(workspace_id, artifact, authority=Authority.MODEL_INFERRED),
        idempotency_key="candidate",
        actor_id="processor",
    )

    assert isinstance(result, CandidateMemory)
    assert result.state is CandidateState.AWAITING_REVIEW
    assert memories.list_memories(workspace_id) == ()


def test_explicit_correction_supersedes_without_overwriting_history(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """A correction creates a new memory and closes the old revision."""
    kernel, _, memories, audit = kernel_parts
    workspace_id = uuid4()
    first_source = source_artifact(workspace_id)
    kernel.capture_source(first_source, idempotency_key="source-1", actor_id="user")
    first = kernel.submit_candidate(
        candidate_memory(workspace_id, first_source),
        idempotency_key="memory-1",
        actor_id="processor",
    )
    assert isinstance(first, MemoryRecord)

    correction_source = source_artifact(
        workspace_id,
        "For documentation, use AsciiDoc instead of Markdown.",
    )
    kernel.capture_source(correction_source, idempotency_key="source-2", actor_id="user")
    correction = kernel.submit_candidate(
        candidate_memory(
            workspace_id,
            correction_source,
            value="AsciiDoc",
            supersedes=(first.id,),
        ),
        idempotency_key="memory-2",
        actor_id="processor",
    )
    assert isinstance(correction, MemoryRecord)

    old = memories.get_memory(first.id)
    assert old is not None
    assert old.status is MemoryStatus.SUPERSEDED
    assert old.revision == 2
    assert len(memories.list_revisions(first.id)) == 2
    assert correction.supersedes == (first.id,)
    assert audit.list_events(workspace_id)[-1].event_type == "MemoryCommitted"


def test_lower_authority_cannot_supersede_explicit_memory(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """An inference cannot revise a stronger explicit assertion."""
    kernel, _, _, _ = kernel_parts
    workspace_id = uuid4()
    artifact = source_artifact(workspace_id)
    kernel.capture_source(artifact, idempotency_key="source-1", actor_id="user")
    first = kernel.submit_candidate(
        candidate_memory(workspace_id, artifact),
        idempotency_key="memory-1",
        actor_id="processor",
    )
    assert isinstance(first, MemoryRecord)

    with pytest.raises(ValidationError, match="lower-authority"):
        kernel.submit_candidate(
            candidate_memory(
                workspace_id,
                artifact,
                authority=Authority.USER_CONFIRMED,
                supersedes=(first.id,),
            ),
            idempotency_key="memory-2",
            actor_id="processor",
        )


def test_forget_uses_optimistic_concurrency_and_excludes_retrieval(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """Forget creates a tombstone revision and stale mutations fail."""
    kernel, _, memories, audit = kernel_parts
    workspace_id = uuid4()
    artifact = source_artifact(workspace_id)
    kernel.capture_source(artifact, idempotency_key="source", actor_id="user")
    committed = kernel.submit_candidate(
        candidate_memory(workspace_id, artifact),
        idempotency_key="memory",
        actor_id="processor",
    )
    assert isinstance(committed, MemoryRecord)

    forgotten = kernel.forget_memory(
        committed.id,
        expected_revision=1,
        actor_id="user",
    )
    assert forgotten.status is MemoryStatus.FORGOTTEN
    with pytest.raises(ConcurrencyError):
        memories.replace_memory(forgotten.model_copy(update={"revision": 3}), 1)

    packet = RetrievalService(memories, audit).retrieve(
        RetrievalRequest(
            query="portable Markdown",
            actor_id="agent",
            purpose="documentation",
            workspace_id=workspace_id,
        )
    )
    assert packet.items == ()


def test_retrieval_filters_scope_sensitivity_and_budget_and_explains_selection(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """Retrieval returns only allowed, scoped memories with optional evidence."""
    kernel, _, memories, audit = kernel_parts
    workspace_id = uuid4()
    project_id = uuid4()
    artifact = source_artifact(workspace_id)
    kernel.capture_source(artifact, idempotency_key="source", actor_id="user")
    committed = kernel.submit_candidate(
        candidate_memory(
            workspace_id,
            artifact,
            scope=MemoryScope(
                project_ids=(project_id,),
                contexts=("documentation",),
            ),
        ),
        idempotency_key="memory",
        actor_id="processor",
    )
    assert isinstance(committed, MemoryRecord)

    packet = RetrievalService(memories, audit).retrieve(
        RetrievalRequest(
            query="portable documentation",
            actor_id="agent",
            purpose="write_docs",
            workspace_id=workspace_id,
            project_ids=(project_id,),
            token_budget=10,
            include_evidence=False,
        )
    )

    assert [item.memory.id for item in packet.items] == [committed.id]
    assert packet.items[0].memory.evidence == ()
    assert "project scope match" in packet.items[0].why_selected
    assert audit.list_events(workspace_id)[-1].trace_id == packet.query_id


def test_retrieval_returns_material_active_contradiction(
    kernel_parts: tuple[
        LearningKernel,
        InMemoryArtifactRepository,
        InMemoryMemoryRepository,
        InMemoryAuditSink,
    ],
) -> None:
    """Selecting a conflicted memory also returns the known active contradiction."""
    kernel, _, memories, audit = kernel_parts
    workspace_id = uuid4()
    first_source = source_artifact(workspace_id)
    kernel.capture_source(first_source, idempotency_key="source-1", actor_id="user")
    first = kernel.submit_candidate(
        candidate_memory(workspace_id, first_source),
        idempotency_key="memory-1",
        actor_id="processor",
    )
    assert isinstance(first, MemoryRecord)

    second_source = source_artifact(
        workspace_id,
        "For documentation, always use rich text.",
    )
    kernel.capture_source(second_source, idempotency_key="source-2", actor_id="user")
    second = kernel.submit_candidate(
        candidate_memory(
            workspace_id,
            second_source,
            value="rich text",
            contradicts=(first.id,),
        ),
        idempotency_key="memory-2",
        actor_id="processor",
    )
    assert isinstance(second, MemoryRecord)

    packet = RetrievalService(memories, audit).retrieve(
        RetrievalRequest(
            query="portable Markdown",
            actor_id="agent",
            purpose="write_docs",
            workspace_id=workspace_id,
        )
    )
    assert packet.items[0].memory.id == first.id
    assert [memory.id for memory in packet.contradictions] == [second.id]
