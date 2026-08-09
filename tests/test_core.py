from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ell.contracts import (
    ApplicationReceipt,
    ConceptVersion,
    CostTrace,
    Episode,
    EvidenceRef,
    LifecycleState,
    Outcome,
    PermissionGrant,
    Reflection,
    Sensitivity,
    SourceArtifact,
    SourceSpan,
)
from ell.core import (
    CoreError,
    ELLCore,
    IdempotencyConflictError,
    PermissionDeniedError,
    ProvenanceError,
)
from ell.identifiers import content_digest, stable_id

NOW = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)


def source(
    workspace: str = "workspace-a",
    *,
    text: str = "Early stakeholder review improved the cross-functional launch.",
    principal: str = "researcher",
    consent: bool = True,
) -> SourceArtifact:
    digest = content_digest(text)
    source_id = stable_id("src", workspace, "synthetic", digest, NOW)
    return SourceArtifact(
        source_id=source_id,
        workspace_id=workspace,
        source_type="synthetic",
        content=text,
        content_hash=digest,
        spans=[SourceSpan(span_id=f"{source_id}:full", start=0, end=len(text), text=text)],
        event_time=NOW,
        observed_time=NOW,
        consent=consent,
        sensitivity=Sensitivity.PRIVATE,
        grants=[PermissionGrant(principal_id=principal, purposes=["research"])],
    )


def ref(artifact: SourceArtifact) -> EvidenceRef:
    return EvidenceRef(source_id=artifact.source_id, span_id=artifact.spans[0].span_id)


def episode(artifact: SourceArtifact) -> Episode:
    evidence = [ref(artifact)]
    return Episode(
        episode_id=stable_id(
            "ep",
            artifact.workspace_id,
            [item.model_dump(mode="json") for item in evidence],
            NOW,
            NOW,
        ),
        workspace_id=artifact.workspace_id,
        context="cross-functional launch",
        observation=artifact.content,
        action="start review early",
        outcome="launch succeeded",
        evidence=evidence,
        event_time_start=NOW,
        event_time_end=NOW,
        observed_time=NOW,
    )


def reflection(artifact: SourceArtifact) -> Reflection:
    return Reflection(
        reflection_id=stable_id("reflection", artifact.source_id),
        workspace_id=artifact.workspace_id,
        statement="Early review may reduce launch risk.",
        reflection_type="causal_hypothesis",
        scope=["cross-functional launch"],
        support=[ref(artifact)],
        counterevidence=[],
        uncertainty=0.25,
        generated_by="fixture-v1",
        observed_time=NOW,
    )


def concept(artifact: SourceArtifact, *, version: int = 1) -> ConceptVersion:
    concept_id = stable_id("concept", artifact.workspace_id, "early-review")
    return ConceptVersion(
        concept_id=concept_id,
        version=version,
        workspace_id=artifact.workspace_id,
        proposition="Start stakeholder review early for cross-functional launches.",
        scope=["cross-functional", "launch"],
        conditions=["external dependencies"],
        implication="start review before implementation is locked",
        support=[ref(artifact)],
        counterevidence=[],
        confidence=0.92,
        valid_from=NOW + timedelta(days=version - 1),
        observed_time=NOW + timedelta(days=version - 1),
        lifecycle_state=LifecycleState.CORROBORATED,
        parent_versions=[] if version == 1 else [f"{concept_id}:v{version - 1}"],
    )


@pytest.fixture
def core() -> ELLCore:
    return ELLCore(clock=lambda: NOW)


def commit_fixture(core: ELLCore, artifact: SourceArtifact) -> ConceptVersion:
    core.record_source(artifact, idempotency_key="source", actor_id="fixture")
    core.record_episode(episode(artifact), idempotency_key="episode", actor_id="fixture")
    proposed = reflection(artifact)
    core.quarantine_reflection(proposed, idempotency_key="reflection", actor_id="model")
    core.review_reflection(
        artifact.workspace_id, proposed.reflection_id, accept=True, actor_id="validator"
    )
    return core.commit_concept(
        concept(artifact),
        validated_reflection_ids=[proposed.reflection_id],
        idempotency_key="concept-v1",
        actor_id="validator",
    )


def test_full_deterministic_lifecycle_resolves_to_source(core: ELLCore) -> None:
    artifact = source()
    committed = commit_fixture(core, artifact)
    assert core.resolve_evidence(artifact.workspace_id, committed.support) == [artifact.content]
    assert len(core.store.evidence_links) == 1
    packet = core.retrieve_learning(
        workspace_id=artifact.workspace_id,
        principal_id="researcher",
        purpose="research",
        query="cross-functional launch review",
        budget=1_000,
    )
    assert packet.concept_versions == [committed.version_id]
    assert packet.evidence == committed.support


def test_model_reflection_is_not_committed_without_review(core: ELLCore) -> None:
    artifact = source()
    core.record_source(artifact, idempotency_key="source", actor_id="fixture")
    proposed = reflection(artifact)
    core.quarantine_reflection(proposed, idempotency_key="reflection", actor_id="model")
    with pytest.raises(CoreError, match="validated reflections"):
        core.commit_concept(
            concept(artifact),
            validated_reflection_ids=[proposed.reflection_id],
            idempotency_key="concept",
            actor_id="validator",
        )


def test_idempotent_retry_returns_same_result_and_conflict_is_rejected(core: ELLCore) -> None:
    artifact = source()
    first = core.record_source(artifact, idempotency_key="same", actor_id="fixture")
    second = core.record_source(artifact, idempotency_key="same", actor_id="fixture")
    assert first == second
    altered = source(text="Different content under the same command key.")
    with pytest.raises(IdempotencyConflictError):
        core.record_source(altered, idempotency_key="same", actor_id="fixture")


def test_source_hash_and_deterministic_identity_are_enforced(core: ELLCore) -> None:
    artifact = source().model_copy(update={"content_hash": "sha256:" + "0" * 64})
    with pytest.raises(ProvenanceError, match="content hash"):
        core.record_source(artifact, idempotency_key="bad", actor_id="fixture")


def test_cross_workspace_evidence_is_rejected(core: ELLCore) -> None:
    artifact = source("workspace-b")
    core.record_source(artifact, idempotency_key="source", actor_id="fixture")
    foreign_episode = episode(artifact).model_copy(update={"workspace_id": "workspace-a"})
    with pytest.raises(PermissionDeniedError, match="another workspace"):
        core.record_episode(foreign_episode, idempotency_key="foreign", actor_id="attacker")


def test_withdrawn_consent_blocks_derived_objects(core: ELLCore) -> None:
    artifact = source(consent=False)
    core.record_source(artifact, idempotency_key="source", actor_id="fixture")
    with pytest.raises(PermissionDeniedError, match="consent"):
        core.record_episode(episode(artifact), idempotency_key="episode", actor_id="fixture")


def test_episode_cannot_lower_source_sensitivity(core: ELLCore) -> None:
    artifact = source().model_copy(update={"sensitivity": Sensitivity.RESTRICTED})
    core.record_source(artifact, idempotency_key="source", actor_id="fixture")
    lowered = episode(artifact).model_copy(update={"sensitivity": Sensitivity.PRIVATE})
    with pytest.raises(PermissionDeniedError, match="lower source sensitivity"):
        core.record_episode(lowered, idempotency_key="episode", actor_id="fixture")


def test_invalid_observed_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="observed time"):
        SourceArtifact.model_validate(
            source().model_copy(update={"observed_time": NOW - timedelta(seconds=1)}).model_dump()
        )


def test_revision_preserves_lineage_and_supersedes_prior_version(core: ELLCore) -> None:
    artifact = source()
    first = commit_fixture(core, artifact)
    second = core.commit_concept(
        concept(artifact, version=2),
        validated_reflection_ids=[reflection(artifact).reflection_id],
        idempotency_key="concept-v2",
        actor_id="validator",
    )
    stored_first = core.store.concepts[(artifact.workspace_id, first.version_id)]
    assert stored_first.lifecycle_state is LifecycleState.SUPERSEDED
    assert stored_first.valid_to == second.valid_from
    assert first.version_id in second.parent_versions


def test_deletion_cascades_and_invalidates_projections(core: ELLCore) -> None:
    artifact = source()
    committed = commit_fixture(core, artifact)
    core.store.projection_ids[artifact.source_id] = {"bm25-7", "vector-9", "external-3"}
    report = core.invalidate_source(artifact.workspace_id, artifact.source_id, actor_id="user")
    assert report.complete
    assert committed.version_id in report.invalidated_ids
    assert report.unreachable_projection_ids == ["bm25-7", "external-3", "vector-9"]
    assert core.store.sources[(artifact.workspace_id, artifact.source_id)].content == ""
    packet = core.retrieve_learning(
        workspace_id=artifact.workspace_id,
        principal_id="researcher",
        purpose="research",
        query="cross-functional launch",
        budget=1_000,
    )
    assert packet.concept_versions == []


def test_application_and_independent_outcome_are_traced(core: ELLCore) -> None:
    artifact = source()
    committed = commit_fixture(core, artifact)
    receipt = ApplicationReceipt(
        application_id="application-1",
        run_id="run-1",
        workspace_id=artifact.workspace_id,
        task_id="task-1",
        selected_record_ids=[],
        concept_versions=[committed.version_id],
        restored_evidence=committed.support,
        decision="start_review_early",
        policy_id="fixture",
        model_id="none",
        cost=CostTrace(input_tokens=10, output_tokens=1),
        observed_time=NOW,
    )
    core.record_application(receipt, idempotency_key="application", actor_id="agent")
    feedback_source = source(text="The launch completed on time after early review.")
    core.record_source(feedback_source, idempotency_key="feedback-source", actor_id="observer")
    outcome = Outcome(
        outcome_id="outcome-1",
        workspace_id=artifact.workspace_id,
        application_id=receipt.application_id,
        value=1.0,
        observation="completed on time",
        source_id=feedback_source.source_id,
        reliability=1.0,
        observed_time=NOW,
    )
    core.record_outcome(outcome, idempotency_key="outcome", actor_id="observer")
    assert core.store.outcomes[(artifact.workspace_id, outcome.outcome_id)] == outcome
    assert core.store.concepts[(artifact.workspace_id, committed.version_id)] == committed
