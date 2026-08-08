"""Stable ports consumed by the provider-neutral learning kernel."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from ell.domain.models import AuditEvent, CandidateMemory, MemoryRecord, SourceArtifact


class ArtifactRepository(Protocol):
    """Canonical source artifact access."""

    def add(self, artifact: SourceArtifact, idempotency_key: str) -> SourceArtifact:
        """Persist an artifact once for an idempotency key."""

    def get(self, artifact_id: UUID) -> SourceArtifact | None:
        """Return an artifact by stable ID."""


class MemoryRepository(Protocol):
    """Canonical candidate and memory persistence."""

    def add_candidate(self, candidate: CandidateMemory) -> CandidateMemory:
        """Store a candidate in quarantine."""

    def replace_candidate(self, candidate: CandidateMemory) -> CandidateMemory:
        """Advance a candidate state without changing its identity."""

    def add_memory(self, memory: MemoryRecord) -> MemoryRecord:
        """Append a canonical memory revision."""

    def get_memory(self, memory_id: UUID) -> MemoryRecord | None:
        """Return a memory by ID."""

    def replace_memory(self, memory: MemoryRecord, expected_revision: int) -> MemoryRecord:
        """Append a lifecycle revision using optimistic concurrency."""

    def list_memories(self, workspace_id: UUID) -> tuple[MemoryRecord, ...]:
        """List the latest revision of all memories in a workspace."""

    def get_idempotent_result(self, key: str) -> MemoryRecord | CandidateMemory | None:
        """Return the prior result for an external mutation key."""

    def save_idempotent_result(self, key: str, result: MemoryRecord | CandidateMemory) -> None:
        """Associate an external mutation key with its result."""


class AuditSink(Protocol):
    """Append-only audit event sink."""

    def append(self, event: AuditEvent) -> None:
        """Append an immutable event."""

    def list_events(self, workspace_id: UUID) -> tuple[AuditEvent, ...]:
        """List workspace events in append order."""
