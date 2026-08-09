"""Deterministic ELL-Core with no model or external storage dependency."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel

from ell.contracts import (
    ApplicationReceipt,
    AuditEvent,
    ConceptVersion,
    Episode,
    EvidenceLink,
    EvidenceRef,
    EvidenceRelation,
    InvalidationReport,
    LearningPacket,
    LifecycleState,
    Outcome,
    Reflection,
    ReviewState,
    Sensitivity,
    SourceArtifact,
)
from ell.identifiers import content_digest, sha256_digest, stable_id


class CoreError(ValueError):
    """Base error for deterministic contract failures."""


class IdempotencyConflictError(CoreError):
    """An idempotency key was reused with a different command."""


class PermissionDeniedError(CoreError):
    """Evidence is outside the caller's workspace or permission envelope."""


class ProvenanceError(CoreError):
    """A derived object cannot resolve its claimed evidence."""


T = TypeVar("T", bound=BaseModel)


@dataclass
class InMemoryStore:
    """Append-oriented canonical state plus rebuildable projection bookkeeping."""

    sources: Dict[Tuple[str, str], SourceArtifact] = field(default_factory=dict)
    episodes: Dict[Tuple[str, str], Episode] = field(default_factory=dict)
    reflections: Dict[Tuple[str, str], Reflection] = field(default_factory=dict)
    concepts: Dict[Tuple[str, str], ConceptVersion] = field(default_factory=dict)
    evidence_links: Dict[Tuple[str, str], EvidenceLink] = field(default_factory=dict)
    applications: Dict[Tuple[str, str], ApplicationReceipt] = field(default_factory=dict)
    outcomes: Dict[Tuple[str, str], Outcome] = field(default_factory=dict)
    audits: List[AuditEvent] = field(default_factory=list)
    idempotency: Dict[Tuple[str, str, str], Tuple[str, BaseModel]] = field(default_factory=dict)
    projection_ids: Dict[str, set[str]] = field(default_factory=dict)


class ELLCore:
    """Sole deterministic authority for canonical lifecycle transitions."""

    _SENSITIVITY_RANK = {
        Sensitivity.PUBLIC: 0,
        Sensitivity.INTERNAL: 1,
        Sensitivity.PRIVATE: 2,
        Sensitivity.RESTRICTED: 3,
    }

    def __init__(
        self,
        store: Optional[InMemoryStore] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.store = store or InMemoryStore()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def record_source(
        self, source: SourceArtifact, *, idempotency_key: str, actor_id: str
    ) -> SourceArtifact:
        """Commit an immutable source after content and identity checks."""
        payload = self._command("record_source", source)
        prior = self._prior(source.workspace_id, "record_source", idempotency_key, payload)
        if prior is not None:
            return self._typed(prior, SourceArtifact)
        if source.content_hash != content_digest(source.content):
            raise ProvenanceError("source content hash does not match content")
        expected = stable_id(
            "src", source.workspace_id, source.source_type, source.content_hash, source.event_time
        )
        if source.source_id != expected:
            raise ProvenanceError("source identifier is not deterministic")
        key = (source.workspace_id, source.source_id)
        existing = self.store.sources.get(key)
        if existing is not None and existing != source:
            raise IdempotencyConflictError("source identity collision")
        self.store.sources[key] = source
        self._remember(source.workspace_id, "record_source", idempotency_key, payload, source)
        self._audit(source.workspace_id, actor_id, "record_source", source.source_id, "accepted")
        return source

    def record_episode(self, episode: Episode, *, idempotency_key: str, actor_id: str) -> Episode:
        """Commit an episode only when every cited span is permitted and resolvable."""
        payload = self._command("record_episode", episode)
        prior = self._prior(episode.workspace_id, "record_episode", idempotency_key, payload)
        if prior is not None:
            return self._typed(prior, Episode)
        self._validate_refs(episode.workspace_id, episode.evidence)
        source_sensitivities = [
            self.store.sources[(episode.workspace_id, item.source_id)].sensitivity
            for item in episode.evidence
        ]
        if any(
            self._SENSITIVITY_RANK[episode.sensitivity] < self._SENSITIVITY_RANK[source_sensitivity]
            for source_sensitivity in source_sensitivities
        ):
            raise PermissionDeniedError("episode cannot lower source sensitivity")
        expected = stable_id(
            "ep",
            episode.workspace_id,
            [ref.model_dump(mode="json") for ref in episode.evidence],
            episode.event_time_start,
            episode.event_time_end,
        )
        if episode.episode_id != expected:
            raise ProvenanceError("episode identifier is not deterministic")
        self._put_once(self.store.episodes, episode.workspace_id, episode.episode_id, episode)
        self._remember(episode.workspace_id, "record_episode", idempotency_key, payload, episode)
        self._audit(
            episode.workspace_id, actor_id, "record_episode", episode.episode_id, "accepted"
        )
        return episode

    def quarantine_reflection(
        self, reflection: Reflection, *, idempotency_key: str, actor_id: str
    ) -> Reflection:
        """Accept generated interpretations only into quarantine."""
        payload = self._command("quarantine_reflection", reflection)
        prior = self._prior(
            reflection.workspace_id, "quarantine_reflection", idempotency_key, payload
        )
        if prior is not None:
            return self._typed(prior, Reflection)
        if reflection.review_state is not ReviewState.QUARANTINED:
            raise CoreError("new reflections must enter quarantine")
        self._validate_refs(
            reflection.workspace_id, [*reflection.support, *reflection.counterevidence]
        )
        self._put_once(
            self.store.reflections,
            reflection.workspace_id,
            reflection.reflection_id,
            reflection,
        )
        self._remember(
            reflection.workspace_id,
            "quarantine_reflection",
            idempotency_key,
            payload,
            reflection,
        )
        self._audit(
            reflection.workspace_id,
            actor_id,
            "quarantine_reflection",
            reflection.reflection_id,
            "model_output_quarantined",
        )
        return reflection

    def review_reflection(
        self, workspace_id: str, reflection_id: str, *, accept: bool, actor_id: str
    ) -> Reflection:
        """Apply a deterministic or human review decision without rewriting content."""
        key = (workspace_id, reflection_id)
        current = self.store.reflections.get(key)
        if current is None:
            raise KeyError(reflection_id)
        if current.review_state is not ReviewState.QUARANTINED:
            raise CoreError("only quarantined reflections may be reviewed")
        state = ReviewState.VALIDATED if accept else ReviewState.REJECTED
        reviewed = current.model_copy(update={"review_state": state})
        self.store.reflections[key] = reviewed
        self._audit(workspace_id, actor_id, "review_reflection", reflection_id, state.value)
        return reviewed

    def commit_concept(
        self,
        concept: ConceptVersion,
        *,
        validated_reflection_ids: List[str],
        idempotency_key: str,
        actor_id: str,
    ) -> ConceptVersion:
        """Commit a version only from permitted evidence and validated reflections."""
        command = {"concept": concept, "reflections": sorted(validated_reflection_ids)}
        payload = self._command("commit_concept", command)
        prior = self._prior(concept.workspace_id, "commit_concept", idempotency_key, payload)
        if prior is not None:
            return self._typed(prior, ConceptVersion)
        self._validate_refs(concept.workspace_id, [*concept.support, *concept.counterevidence])
        for reflection_id in validated_reflection_ids:
            reflection = self.store.reflections.get((concept.workspace_id, reflection_id))
            if reflection is None or reflection.review_state is not ReviewState.VALIDATED:
                raise CoreError("concept requires validated reflections")
        prior_versions = self._concept_versions(concept.workspace_id, concept.concept_id)
        expected_version = len(prior_versions) + 1
        if concept.version != expected_version:
            raise CoreError(f"expected concept version {expected_version}")
        if concept.version == 1 and concept.parent_versions:
            raise CoreError("first concept version cannot have parents")
        if concept.version > 1:
            expected_parent = prior_versions[-1].version_id
            if expected_parent not in concept.parent_versions:
                raise CoreError("new concept version must cite its immediate parent")
            old = prior_versions[-1]
            if old.lifecycle_state in {LifecycleState.DELETED, LifecycleState.RETIRED}:
                raise CoreError("deleted or retired concepts cannot be revised")
            superseded = old.model_copy(
                update={
                    "lifecycle_state": LifecycleState.SUPERSEDED,
                    "valid_to": concept.valid_from,
                }
            )
            self.store.concepts[(concept.workspace_id, old.version_id)] = superseded
        self._put_once(self.store.concepts, concept.workspace_id, concept.version_id, concept)
        for ref in [*concept.support, *concept.counterevidence]:
            relation = (
                EvidenceRelation.SUPPORTS
                if ref in concept.support
                else EvidenceRelation.CONTRADICTS
            )
            link = EvidenceLink(
                link_id=stable_id("link", concept.version_id, ref.source_id, ref.span_id, relation),
                workspace_id=concept.workspace_id,
                source=ref,
                target_id=concept.concept_id,
                target_version=concept.version,
                relation=relation,
                method="deterministic_commit",
                validator=actor_id,
                observed_time=self._clock(),
            )
            self.store.evidence_links[(concept.workspace_id, link.link_id)] = link
        self._remember(concept.workspace_id, "commit_concept", idempotency_key, payload, concept)
        self._audit(
            concept.workspace_id,
            actor_id,
            "commit_concept",
            concept.version_id,
            "validated_evidence",
            prior_version=concept.parent_versions[-1] if concept.parent_versions else None,
            new_version=concept.version_id,
        )
        return concept

    def retrieve_learning(
        self,
        *,
        workspace_id: str,
        principal_id: str,
        purpose: str,
        query: str,
        budget: int,
    ) -> LearningPacket:
        """Return lexical matches whose exact evidence is currently permitted."""
        query_terms = set(self._terms(query))
        ranked: List[Tuple[float, ConceptVersion, List[EvidenceRef]]] = []
        for concept in self._concept_versions(workspace_id):
            if concept.lifecycle_state not in {
                LifecycleState.CORROBORATED,
                LifecycleState.CONTESTED,
                LifecycleState.REVISED,
            }:
                continue
            evidence = [*concept.support, *concept.counterevidence]
            if not all(
                self._ref_allowed(workspace_id, ref, principal_id, purpose) for ref in evidence
            ):
                continue
            terms = set(self._terms(" ".join([concept.proposition, *concept.scope])))
            overlap = len(query_terms & terms)
            if overlap:
                ranked.append((overlap * concept.confidence, concept, evidence))
        ranked.sort(key=lambda item: (-item[0], item[1].version_id))
        selected: List[str] = []
        restored: List[EvidenceRef] = []
        conflicts: List[EvidenceRef] = []
        used = 0
        uncertainties: List[float] = []
        for _, concept, _ in ranked:
            cost = len(concept.proposition) + sum(
                len(self._resolve_ref(workspace_id, ref).text)
                for ref in [*concept.support, *concept.counterevidence]
            )
            if used + cost > budget:
                continue
            selected.append(concept.version_id)
            restored.extend(concept.support)
            conflicts.extend(concept.counterevidence)
            uncertainties.append(1.0 - concept.confidence)
            used += cost
        return LearningPacket(
            workspace_id=workspace_id,
            query=query,
            concept_versions=selected,
            evidence=restored,
            conflicts=conflicts,
            uncertainty=max(uncertainties, default=1.0),
            budget_used=used,
        )

    def record_application(
        self, receipt: ApplicationReceipt, *, idempotency_key: str, actor_id: str
    ) -> ApplicationReceipt:
        """Record exactly what governed context affected a decision."""
        payload = self._command("record_application", receipt)
        prior = self._prior(receipt.workspace_id, "record_application", idempotency_key, payload)
        if prior is not None:
            return self._typed(prior, ApplicationReceipt)
        self._validate_refs(receipt.workspace_id, receipt.restored_evidence)
        for version_id in receipt.concept_versions:
            if (receipt.workspace_id, version_id) not in self.store.concepts:
                raise ProvenanceError("application cites an unknown concept version")
        self._put_once(
            self.store.applications, receipt.workspace_id, receipt.application_id, receipt
        )
        self._remember(
            receipt.workspace_id, "record_application", idempotency_key, payload, receipt
        )
        self._audit(
            receipt.workspace_id,
            actor_id,
            "record_application",
            receipt.application_id,
            "receipt_complete",
        )
        return receipt

    def record_outcome(self, outcome: Outcome, *, idempotency_key: str, actor_id: str) -> Outcome:
        """Attach independently sourced feedback without mutating concepts."""
        payload = self._command("record_outcome", outcome)
        prior = self._prior(outcome.workspace_id, "record_outcome", idempotency_key, payload)
        if prior is not None:
            return self._typed(prior, Outcome)
        if (outcome.workspace_id, outcome.application_id) not in self.store.applications:
            raise ProvenanceError("outcome cites an unknown application")
        if (outcome.workspace_id, outcome.source_id) not in self.store.sources:
            raise ProvenanceError("outcome source does not exist")
        self._put_once(self.store.outcomes, outcome.workspace_id, outcome.outcome_id, outcome)
        self._remember(outcome.workspace_id, "record_outcome", idempotency_key, payload, outcome)
        self._audit(
            outcome.workspace_id,
            actor_id,
            "record_outcome",
            outcome.outcome_id,
            "independent_feedback",
        )
        return outcome

    def invalidate_source(
        self, workspace_id: str, source_id: str, *, actor_id: str
    ) -> InvalidationReport:
        """Tombstone evidence and every dependent canonical/projection object."""
        key = (workspace_id, source_id)
        source = self.store.sources.get(key)
        if source is None:
            raise KeyError(source_id)
        if source.tombstoned:
            prior_reports = [
                audit.audit_id
                for audit in self.store.audits
                if audit.workspace_id == workspace_id
                and audit.operation == "invalidate_source"
                and audit.object_id == source_id
            ]
            return InvalidationReport(
                workspace_id=workspace_id,
                source_id=source_id,
                invalidated_ids=[],
                retained_audit_ids=prior_reports,
                unreachable_projection_ids=[],
                complete=True,
            )
        self.store.sources[key] = source.model_copy(
            update={"content": "", "spans": [], "tombstoned": True}
        )
        invalidated: List[str] = [source_id]
        for object_key, episode in list(self.store.episodes.items()):
            if object_key[0] == workspace_id and any(
                ref.source_id == source_id for ref in episode.evidence
            ):
                self.store.episodes[object_key] = episode.model_copy(update={"tombstoned": True})
                invalidated.append(episode.episode_id)
        for object_key, reflection in list(self.store.reflections.items()):
            refs = [*reflection.support, *reflection.counterevidence]
            if object_key[0] == workspace_id and any(ref.source_id == source_id for ref in refs):
                self.store.reflections[object_key] = reflection.model_copy(
                    update={"review_state": ReviewState.REJECTED}
                )
                invalidated.append(reflection.reflection_id)
        for object_key, concept in list(self.store.concepts.items()):
            refs = [*concept.support, *concept.counterevidence]
            if object_key[0] == workspace_id and any(ref.source_id == source_id for ref in refs):
                self.store.concepts[object_key] = concept.model_copy(
                    update={"lifecycle_state": LifecycleState.DELETED, "valid_to": self._clock()}
                )
                invalidated.append(concept.version_id)
        unreachable = sorted(self.store.projection_ids.pop(source_id, set()))
        audit = self._audit(
            workspace_id, actor_id, "invalidate_source", source_id, "deletion_cascade_complete"
        )
        return InvalidationReport(
            workspace_id=workspace_id,
            source_id=source_id,
            invalidated_ids=sorted(invalidated),
            retained_audit_ids=[audit.audit_id],
            unreachable_projection_ids=unreachable,
            complete=True,
        )

    def resolve_evidence(self, workspace_id: str, refs: List[EvidenceRef]) -> List[str]:
        """Resolve exact permitted source text for invariant tests and explanations."""
        return [self._resolve_ref(workspace_id, ref).text for ref in refs]

    def _validate_refs(self, workspace_id: str, refs: List[EvidenceRef]) -> None:
        for ref in refs:
            self._resolve_ref(workspace_id, ref)

    def _resolve_ref(self, workspace_id: str, ref: EvidenceRef) -> Any:
        source = self.store.sources.get((workspace_id, ref.source_id))
        if source is None:
            if any(key[1] == ref.source_id for key in self.store.sources):
                raise PermissionDeniedError("evidence belongs to another workspace")
            raise ProvenanceError("evidence source does not exist")
        if source.tombstoned or not source.consent:
            raise PermissionDeniedError("evidence is deleted or consent is withdrawn")
        span = next((item for item in source.spans if item.span_id == ref.span_id), None)
        if span is None:
            raise ProvenanceError("evidence span does not exist")
        return span

    def _ref_allowed(
        self, workspace_id: str, ref: EvidenceRef, principal_id: str, purpose: str
    ) -> bool:
        try:
            self._resolve_ref(workspace_id, ref)
        except CoreError:
            return False
        source = self.store.sources[(workspace_id, ref.source_id)]
        return any(
            grant.principal_id == principal_id and purpose in grant.purposes
            for grant in source.grants
        )

    def _concept_versions(
        self, workspace_id: str, concept_id: Optional[str] = None
    ) -> List[ConceptVersion]:
        concepts = [
            concept
            for (workspace, _), concept in self.store.concepts.items()
            if workspace == workspace_id
            and (concept_id is None or concept.concept_id == concept_id)
        ]
        return sorted(concepts, key=lambda item: (item.concept_id, item.version))

    def _audit(
        self,
        workspace_id: str,
        actor_id: str,
        operation: str,
        object_id: str,
        reason: str,
        *,
        prior_version: Optional[str] = None,
        new_version: Optional[str] = None,
    ) -> AuditEvent:
        sequence = sum(1 for item in self.store.audits if item.workspace_id == workspace_id)
        audit = AuditEvent(
            audit_id=stable_id("audit", workspace_id, sequence, operation, object_id),
            workspace_id=workspace_id,
            actor_id=actor_id,
            operation=operation,
            object_id=object_id,
            prior_version=prior_version,
            new_version=new_version,
            method="ell_core",
            reason_code=reason,
            observed_time=self._clock(),
        )
        self.store.audits.append(audit)
        return audit

    @staticmethod
    def _terms(text: str) -> List[str]:
        return [token.strip(".,:;!?()[]{}\"'").lower() for token in text.split() if token]

    @staticmethod
    def _command(operation: str, value: Any) -> str:
        return sha256_digest({"operation": operation, "value": value})

    def _prior(
        self, workspace_id: str, operation: str, key: str, payload: str
    ) -> Optional[BaseModel]:
        prior = self.store.idempotency.get((workspace_id, operation, key))
        if prior is None:
            return None
        prior_payload, result = prior
        if prior_payload != payload:
            raise IdempotencyConflictError("idempotency key reused with different payload")
        return result

    def _remember(
        self,
        workspace_id: str,
        operation: str,
        key: str,
        payload: str,
        result: BaseModel,
    ) -> None:
        self.store.idempotency[(workspace_id, operation, key)] = (payload, result)

    @staticmethod
    def _put_once(store: Dict[Tuple[str, str], T], workspace: str, key: str, value: T) -> None:
        existing = store.get((workspace, key))
        if existing is not None and existing != value:
            raise IdempotencyConflictError("canonical identity collision")
        store[(workspace, key)] = value

    @staticmethod
    def _typed(value: BaseModel, expected: Type[T]) -> T:
        if not isinstance(value, expected):
            raise TypeError("stored idempotent result has wrong type")
        return value
