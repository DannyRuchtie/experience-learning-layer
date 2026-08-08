"""Deterministic in-memory adapters used by tests and the Phase 0 kernel."""

from __future__ import annotations

from uuid import UUID

from ell.domain.models import AuditEvent, CandidateMemory, MemoryRecord, SourceArtifact


class ConcurrencyError(RuntimeError):
    """Raised when a caller mutates a stale memory revision."""


class InMemoryArtifactRepository:
    """In-memory canonical artifact adapter with idempotent capture."""

    def __init__(self) -> None:
        self._artifacts: dict[UUID, SourceArtifact] = {}
        self._idempotency: dict[str, UUID] = {}

    def add(self, artifact: SourceArtifact, idempotency_key: str) -> SourceArtifact:
        """Store an artifact, returning the first result for repeated capture."""
        existing_id = self._idempotency.get(idempotency_key)
        if existing_id is not None:
            return self._artifacts[existing_id]
        self._artifacts[artifact.id] = artifact
        self._idempotency[idempotency_key] = artifact.id
        return artifact

    def get(self, artifact_id: UUID) -> SourceArtifact | None:
        """Return an artifact by stable ID."""
        return self._artifacts.get(artifact_id)


class InMemoryMemoryRepository:
    """In-memory adapter that retains every canonical memory revision."""

    def __init__(self) -> None:
        self._candidates: dict[UUID, CandidateMemory] = {}
        self._revisions: dict[UUID, list[MemoryRecord]] = {}
        self._idempotency: dict[str, MemoryRecord | CandidateMemory] = {}

    def add_candidate(self, candidate: CandidateMemory) -> CandidateMemory:
        """Store a new candidate in quarantine."""
        if candidate.id in self._candidates:
            raise ValueError(f"candidate already exists: {candidate.id}")
        self._candidates[candidate.id] = candidate
        return candidate

    def replace_candidate(self, candidate: CandidateMemory) -> CandidateMemory:
        """Advance candidate state while preserving the immutable prior value externally."""
        if candidate.id not in self._candidates:
            raise KeyError(candidate.id)
        self._candidates[candidate.id] = candidate
        return candidate

    def add_memory(self, memory: MemoryRecord) -> MemoryRecord:
        """Append the first revision of a canonical memory."""
        if memory.id in self._revisions:
            raise ValueError(f"memory already exists: {memory.id}")
        self._revisions[memory.id] = [memory]
        return memory

    def get_memory(self, memory_id: UUID) -> MemoryRecord | None:
        """Return the latest revision of a memory."""
        revisions = self._revisions.get(memory_id)
        return revisions[-1] if revisions else None

    def replace_memory(self, memory: MemoryRecord, expected_revision: int) -> MemoryRecord:
        """Append a revision after an optimistic-concurrency check."""
        revisions = self._revisions.get(memory.id)
        if not revisions:
            raise KeyError(memory.id)
        current = revisions[-1]
        if current.revision != expected_revision:
            raise ConcurrencyError(
                f"expected revision {expected_revision}, current revision is {current.revision}"
            )
        if memory.revision != expected_revision + 1:
            raise ValueError("replacement revision must increment by exactly one")
        revisions.append(memory)
        return memory

    def list_memories(self, workspace_id: UUID) -> tuple[MemoryRecord, ...]:
        """Return the latest revision for each workspace memory."""
        return tuple(
            revisions[-1]
            for revisions in self._revisions.values()
            if revisions[-1].workspace_id == workspace_id
        )

    def list_revisions(self, memory_id: UUID) -> tuple[MemoryRecord, ...]:
        """Return immutable history for inspection and tests."""
        return tuple(self._revisions.get(memory_id, ()))

    def get_candidate(self, candidate_id: UUID) -> CandidateMemory | None:
        """Return the current candidate state."""
        return self._candidates.get(candidate_id)

    def get_idempotent_result(self, key: str) -> MemoryRecord | CandidateMemory | None:
        """Return a result previously saved for an external mutation key."""
        return self._idempotency.get(key)

    def save_idempotent_result(self, key: str, result: MemoryRecord | CandidateMemory) -> None:
        """Save the first result produced for an external mutation key."""
        self._idempotency.setdefault(key, result)


class InMemoryAuditSink:
    """Content-minimized append-only audit adapter."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        """Append an immutable audit event."""
        self._events.append(event)

    def list_events(self, workspace_id: UUID) -> tuple[AuditEvent, ...]:
        """List events for one workspace in append order."""
        return tuple(event for event in self._events if event.workspace_id == workspace_id)
