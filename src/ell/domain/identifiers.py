"""Deterministic source identity helpers for rerunnable ingestion."""

from __future__ import annotations

from uuid import UUID, uuid5

ELL_NAMESPACE = UUID("57d81e68-b0d4-5031-9dbf-cd69aa4edfd2")


def stable_source_id(connector: str, external_ref: str, version: str = "1") -> UUID:
    """Derive the same stable UUID for the same provider record and version."""
    if not connector.strip() or not external_ref.strip() or not version.strip():
        raise ValueError("connector, external_ref, and version must be non-empty")
    return uuid5(ELL_NAMESPACE, f"source:{connector}:{external_ref}:{version}")


def stable_event_id(source_id: UUID, source_event_id: str) -> UUID:
    """Derive the same stable UUID for an event inside a captured source."""
    if not source_event_id.strip():
        raise ValueError("source_event_id must be non-empty")
    return uuid5(source_id, f"event:{source_event_id}")


def stable_episode_id(workspace_id: UUID, event_ids: tuple[UUID, ...]) -> UUID:
    """Derive an order-sensitive stable ID for a normalized event group."""
    if not event_ids:
        raise ValueError("an episode requires at least one event")
    joined = ":".join(str(event_id) for event_id in event_ids)
    return uuid5(workspace_id, f"episode:{joined}")
