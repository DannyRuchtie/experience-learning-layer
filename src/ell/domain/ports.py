"""Stable ports consumed by the provider-neutral learning kernel."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from ell.domain.models import (
    AuditEvent,
    CandidateMemory,
    Episode,
    ExperienceEvent,
    MemoryRecord,
    SourceArtifact,
)


class ArtifactRepository(Protocol):
    """Canonical source artifact access."""

    def add(self, artifact: SourceArtifact, idempotency_key: str) -> SourceArtifact:
        """Persist an artifact once for an idempotency key."""

    def get(self, artifact_id: UUID) -> SourceArtifact | None:
        """Return an artifact by stable ID."""


class ExperienceLedger(Protocol):
    """Append-only normalized event and episode storage."""

    def append_event(self, event: ExperienceEvent) -> ExperienceEvent:
        """Append an event idempotently by its stable identifier."""

    def get_event(self, event_id: UUID) -> ExperienceEvent | None:
        """Return one normalized event."""

    def list_session_events(
        self, workspace_id: UUID, session_id: str
    ) -> tuple[ExperienceEvent, ...]:
        """Return one session's events in occurrence order."""

    def append_episode(self, episode: Episode) -> Episode:
        """Append a bounded episode idempotently by its stable identifier."""

    def get_episode(self, episode_id: UUID) -> Episode | None:
        """Return one episode."""

    def list_episodes(self, workspace_id: UUID) -> tuple[Episode, ...]:
        """Return workspace episodes in start-time order."""


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
