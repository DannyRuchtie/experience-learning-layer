"""Application services for governed learning and explainable retrieval."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import UUID

from ell.domain.models import (
    AUTHORITY_WEIGHT,
    SENSITIVITY_RANK,
    AuditEvent,
    CandidateMemory,
    CandidateState,
    EvidencePacket,
    EvidenceRelation,
    MemoryRecord,
    MemoryStatus,
    RetrievalItem,
    RetrievalRequest,
    SourceArtifact,
)
from ell.domain.policy import CommitPolicy, PolicyAction
from ell.domain.ports import ArtifactRepository, AuditSink, MemoryRepository


class ValidationError(ValueError):
    """Raised when a candidate violates deterministic domain validation."""


class LearningKernel:
    """Sole coordinator for validated candidate-to-memory lifecycle operations."""

    def __init__(
        self,
        artifacts: ArtifactRepository,
        memories: MemoryRepository,
        audit: AuditSink,
        policy: CommitPolicy | None = None,
    ) -> None:
        self._artifacts = artifacts
        self._memories = memories
        self._audit = audit
        self._policy = policy or CommitPolicy()

    def capture_source(
        self,
        artifact: SourceArtifact,
        *,
        idempotency_key: str,
        actor_id: str,
        purpose: str = "capture",
    ) -> SourceArtifact:
        """Capture an immutable source exactly once and record safe audit metadata."""
        stored = self._artifacts.add(artifact, idempotency_key)
        if stored.id == artifact.id:
            self._audit.append(
                AuditEvent(
                    workspace_id=stored.workspace_id,
                    event_type="SourceCaptured",
                    actor_id=actor_id,
                    purpose=purpose,
                    affected_ids=(stored.id,),
                    policy_reason="source capture accepted",
                )
            )
        return stored

    def submit_candidate(
        self,
        candidate: CandidateMemory,
        *,
        idempotency_key: str,
        actor_id: str,
        purpose: str = "learn",
    ) -> MemoryRecord | CandidateMemory:
        """Validate, apply policy, and either commit, quarantine, or reject a candidate."""
        prior = self._memories.get_idempotent_result(idempotency_key)
        if prior is not None:
            return prior

        self._memories.add_candidate(candidate)
        self._validate_candidate(candidate)
        validated = candidate.model_copy(update={"state": CandidateState.VALIDATED})
        self._memories.replace_candidate(validated)
        decision = self._policy.evaluate(validated)

        result: MemoryRecord | CandidateMemory
        if decision.action is PolicyAction.REJECT:
            rejected = validated.model_copy(update={"state": CandidateState.REJECTED})
            self._memories.replace_candidate(rejected)
            result = rejected
            event_type = "MemoryCandidateRejected"
        elif decision.action is PolicyAction.AWAIT_REVIEW:
            result = validated.model_copy(update={"state": CandidateState.AWAITING_REVIEW})
            self._memories.replace_candidate(result)
            event_type = "MemoryCandidateAwaitingReview"
        else:
            result = self._commit(validated)
            self._memories.replace_candidate(
                validated.model_copy(update={"state": CandidateState.AUTO_COMMITTED})
            )
            event_type = "MemoryCommitted"

        self._memories.save_idempotent_result(idempotency_key, result)
        self._audit.append(
            AuditEvent(
                workspace_id=candidate.workspace_id,
                event_type=event_type,
                actor_id=actor_id,
                purpose=purpose,
                affected_ids=(result.id,),
                policy_reason=decision.reason,
            )
        )
        return result

    def forget_memory(
        self,
        memory_id: UUID,
        *,
        expected_revision: int,
        actor_id: str,
        purpose: str = "forget",
    ) -> MemoryRecord:
        """Immediately tombstone a memory so normal retrieval cannot return it."""
        current = self._memories.get_memory(memory_id)
        if current is None:
            raise KeyError(memory_id)
        forgotten = current.model_copy(
            update={
                "status": MemoryStatus.FORGOTTEN,
                "valid_to": datetime.now(timezone.utc),
                "revision": current.revision + 1,
            }
        )
        stored = self._memories.replace_memory(forgotten, expected_revision)
        self._audit.append(
            AuditEvent(
                workspace_id=stored.workspace_id,
                event_type="MemoryForgotten",
                actor_id=actor_id,
                purpose=purpose,
                affected_ids=(stored.id,),
                policy_reason="explicit forget request",
            )
        )
        return stored

    def _validate_candidate(self, candidate: CandidateMemory) -> None:
        for citation in candidate.evidence:
            artifact = self._artifacts.get(citation.source_id)
            if artifact is None:
                raise ValidationError(f"evidence source does not exist: {citation.source_id}")
            if artifact.workspace_id != candidate.workspace_id:
                raise ValidationError("evidence source belongs to another workspace")
            if not any(span.id == citation.span_id for span in artifact.spans):
                raise ValidationError(f"evidence span does not exist: {citation.span_id}")
            if SENSITIVITY_RANK[candidate.sensitivity] < SENSITIVITY_RANK[artifact.sensitivity]:
                raise ValidationError("candidate cannot lower source sensitivity")

        support_count = sum(
            citation.relation is EvidenceRelation.SUPPORTS for citation in candidate.evidence
        )
        if candidate.evidence and support_count == 0:
            raise ValidationError("candidate requires at least one supporting citation")

        for memory_id in (*candidate.supersedes, *candidate.contradicts):
            memory = self._memories.get_memory(memory_id)
            if memory is None:
                raise ValidationError(f"referenced memory does not exist: {memory_id}")
            if memory.workspace_id != candidate.workspace_id:
                raise ValidationError("referenced memory belongs to another workspace")

    def _commit(self, candidate: CandidateMemory) -> MemoryRecord:
        committed_at = datetime.now(timezone.utc)
        for superseded_id in candidate.supersedes:
            current = self._memories.get_memory(superseded_id)
            if current is None:
                raise ValidationError(f"superseded memory does not exist: {superseded_id}")
            if current.status is not MemoryStatus.ACTIVE:
                raise ValidationError("only active memories can be superseded")
            if AUTHORITY_WEIGHT[candidate.authority] < AUTHORITY_WEIGHT[current.authority]:
                raise ValidationError("lower-authority candidates cannot supersede memory")
            superseded = current.model_copy(
                update={
                    "status": MemoryStatus.SUPERSEDED,
                    "valid_to": committed_at,
                    "revision": current.revision + 1,
                }
            )
            self._memories.replace_memory(superseded, current.revision)

        memory = MemoryRecord(
            workspace_id=candidate.workspace_id,
            memory_type=candidate.memory_type,
            subject_id=candidate.subject_id,
            predicate=candidate.predicate,
            object=candidate.object,
            scope=candidate.scope,
            authority=candidate.authority,
            confidence=candidate.confidence,
            salience=candidate.salience,
            valid_from=candidate.valid_from or candidate.observed_at,
            valid_to=candidate.valid_to,
            observed_at=candidate.observed_at,
            committed_at=committed_at,
            evidence=candidate.evidence,
            derived_by=candidate.derived_by,
            supersedes=candidate.supersedes,
            contradicts=candidate.contradicts,
            sensitivity=candidate.sensitivity,
        )
        return self._memories.add_memory(memory)


class RetrievalService:
    """Deterministic lexical retrieval with policy filters and explanations."""

    _TOKEN_PATTERN = re.compile(r"[\w'-]+", re.UNICODE)

    def __init__(self, memories: MemoryRepository, audit: AuditSink) -> None:
        self._memories = memories
        self._audit = audit

    def retrieve(self, request: RetrievalRequest) -> EvidencePacket:
        """Return an authorized evidence packet within the requested context budget."""
        query_terms = self._terms(request.query)
        candidates: list[RetrievalItem] = []
        for memory in self._memories.list_memories(request.workspace_id):
            if not self._allowed(memory, request):
                continue
            searchable = " ".join((memory.predicate, memory.object.value, *memory.scope.contexts))
            overlap = query_terms & self._terms(searchable)
            if not overlap:
                continue
            lexical = len(overlap) / max(len(query_terms), 1)
            score = lexical * AUTHORITY_WEIGHT[memory.authority] * memory.confidence
            why = ["lexical query match", f"authority: {memory.authority.value}"]
            if request.project_ids and memory.scope.project_ids:
                why.append("project scope match")
            candidates.append(
                RetrievalItem(
                    memory=self._redact_evidence(memory, request.include_evidence),
                    score=score,
                    why_selected=tuple(why),
                )
            )

        candidates.sort(key=lambda item: (item.score, item.memory.salience), reverse=True)
        selected: list[RetrievalItem] = []
        estimated_tokens = 0
        for item in candidates:
            item_tokens = self._estimate_tokens(item.memory.object.value)
            if estimated_tokens + item_tokens > request.token_budget:
                continue
            selected.append(item)
            estimated_tokens += item_tokens

        contradictions: list[MemoryRecord] = []
        contradiction_ids = {
            contradiction_id for item in selected for contradiction_id in item.memory.contradicts
        }
        selected_ids = {item.memory.id for item in selected}
        contradiction_ids.update(
            memory.id
            for memory in self._memories.list_memories(request.workspace_id)
            if selected_ids.intersection(memory.contradicts)
        )
        for contradiction_id in contradiction_ids:
            contradiction = self._memories.get_memory(contradiction_id)
            if contradiction and self._allowed(contradiction, request):
                contradictions.append(
                    self._redact_evidence(contradiction, request.include_evidence)
                )
                estimated_tokens += self._estimate_tokens(contradiction.object.value)

        packet = EvidencePacket(
            items=tuple(selected),
            contradictions=tuple(contradictions),
            estimated_tokens=estimated_tokens,
        )
        self._audit.append(
            AuditEvent(
                workspace_id=request.workspace_id,
                event_type="MemoriesRetrieved",
                actor_id=request.actor_id,
                purpose=request.purpose,
                affected_ids=tuple(item.memory.id for item in selected),
                policy_reason="workspace, lifecycle, scope, type, and sensitivity filters applied",
                trace_id=packet.query_id,
            )
        )
        return packet

    @staticmethod
    def _allowed(memory: MemoryRecord, request: RetrievalRequest) -> bool:
        if memory.status is not MemoryStatus.ACTIVE:
            return False
        if memory.memory_type not in request.allowed_memory_types:
            return False
        if SENSITIVITY_RANK[memory.sensitivity] > SENSITIVITY_RANK[request.maximum_sensitivity]:
            return False
        if request.project_ids and memory.scope.project_ids:
            return bool(set(request.project_ids) & set(memory.scope.project_ids))
        return True

    @classmethod
    def _terms(cls, text: str) -> set[str]:
        return {match.group(0).casefold() for match in cls._TOKEN_PATTERN.finditer(text)}

    @classmethod
    def _estimate_tokens(cls, text: str) -> int:
        return max(1, int(len(cls._TOKEN_PATTERN.findall(text)) * 1.35))

    @staticmethod
    def _redact_evidence(memory: MemoryRecord, include_evidence: bool) -> MemoryRecord:
        return memory if include_evidence else memory.model_copy(update={"evidence": ()})
