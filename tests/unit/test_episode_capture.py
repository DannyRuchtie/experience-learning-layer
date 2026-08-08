"""Tests for deterministic live-chat event and episode capture."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from ell.domain.identifiers import stable_event_id, stable_source_id
from ell.domain.models import EventType, ExperienceEvent, Sensitivity, SourceArtifact, SourceKind
from ell.domain.repositories import (
    InMemoryArtifactRepository,
    InMemoryAuditSink,
    InMemoryExperienceLedger,
)
from ell.domain.services import EpisodeCaptureService, ValidationError

NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def capture_message(
    artifacts: InMemoryArtifactRepository,
    service: EpisodeCaptureService,
    workspace_id: UUID,
    session_id: str,
    message_id: str,
    text: str,
    event_type: EventType,
    occurred_at: datetime,
) -> ExperienceEvent:
    """Capture one exact message source and its normalized event."""
    source_id = stable_source_id("ell_chat", message_id)
    artifact = SourceArtifact(
        id=source_id,
        workspace_id=workspace_id,
        kind=SourceKind.CONVERSATION,
        connector="ell_chat",
        external_ref=message_id,
        content_hash=f"sha256:{hashlib.sha256(text.encode()).hexdigest()}",
        normalized_text=text,
        observed_at=occurred_at,
        sensitivity=Sensitivity.PRIVATE,
    )
    artifacts.add(artifact, idempotency_key=f"source:{message_id}")
    event = ExperienceEvent(
        id=stable_event_id(source_id, message_id),
        workspace_id=workspace_id,
        source_id=source_id,
        source_event_id=message_id,
        session_id=session_id,
        event_type=event_type,
        actor_id="local-user" if event_type is EventType.USER_MESSAGE else "provider:mock",
        occurred_at=occurred_at,
        payload={"text": text, "provider": "mock", "model": "fixture-v1"},
    )
    return service.capture_event(event, actor_id=event.actor_id)


def test_completed_turn_becomes_one_replay_safe_episode() -> None:
    """User input and assistant output remain exact evidence for one bounded episode."""
    artifacts = InMemoryArtifactRepository()
    experiences = InMemoryExperienceLedger()
    audit = InMemoryAuditSink()
    service = EpisodeCaptureService(artifacts, experiences, audit)
    workspace_id = uuid4()

    user = capture_message(
        artifacts,
        service,
        workspace_id,
        "session-1",
        "message-1",
        "Help me capture this experience.",
        EventType.USER_MESSAGE,
        NOW,
    )
    assistant = capture_message(
        artifacts,
        service,
        workspace_id,
        "session-1",
        "message-2",
        "I will preserve it as evidence first.",
        EventType.ASSISTANT_MESSAGE,
        NOW + timedelta(seconds=1),
    )

    first = service.close_episode((user.id, assistant.id), actor_id="local-user")
    second = service.close_episode((user.id, assistant.id), actor_id="local-user")

    assert second == first
    assert first.input == "Help me capture this experience."
    assert first.response == "I will preserve it as evidence first."
    assert first.metadata["boundary"] == "completed_turn"
    assert experiences.list_episodes(workspace_id) == (first,)
    assert [event.event_type for event in audit.list_events(workspace_id)] == [
        "ExperienceEventCaptured",
        "ExperienceEventCaptured",
        "EpisodeClosed",
    ]


def test_event_requires_an_existing_same_workspace_source() -> None:
    """Live capture cannot create provenance-free or cross-workspace events."""
    artifacts = InMemoryArtifactRepository()
    experiences = InMemoryExperienceLedger()
    service = EpisodeCaptureService(artifacts, experiences, InMemoryAuditSink())
    source_id = stable_source_id("ell_chat", "missing")
    event = ExperienceEvent(
        id=stable_event_id(source_id, "missing"),
        workspace_id=uuid4(),
        source_id=source_id,
        source_event_id="missing",
        session_id="session",
        event_type=EventType.USER_MESSAGE,
        actor_id="local-user",
        occurred_at=NOW,
        payload={"text": "Not grounded"},
    )

    with pytest.raises(ValidationError, match="source does not exist"):
        service.capture_event(event, actor_id="local-user")


def test_episode_rejects_cross_session_or_out_of_order_events() -> None:
    """A model cannot silently join unrelated sessions or rewrite chronology."""
    artifacts = InMemoryArtifactRepository()
    experiences = InMemoryExperienceLedger()
    service = EpisodeCaptureService(artifacts, experiences, InMemoryAuditSink())
    workspace_id = uuid4()
    first = capture_message(
        artifacts,
        service,
        workspace_id,
        "session-1",
        "message-1",
        "First",
        EventType.USER_MESSAGE,
        NOW,
    )
    second = capture_message(
        artifacts,
        service,
        workspace_id,
        "session-2",
        "message-2",
        "Second",
        EventType.ASSISTANT_MESSAGE,
        NOW + timedelta(seconds=1),
    )

    with pytest.raises(ValidationError, match="different sessions"):
        service.close_episode((first.id, second.id), actor_id="local-user")

    same_session_second = second.model_copy(update={"session_id": "session-1"})
    experiences = InMemoryExperienceLedger()
    service = EpisodeCaptureService(artifacts, experiences, InMemoryAuditSink())
    service.capture_event(first, actor_id="local-user")
    service.capture_event(same_session_second, actor_id="provider:mock")
    with pytest.raises(ValidationError, match="occurrence order"):
        service.close_episode((same_session_second.id, first.id), actor_id="local-user")
