"""Versioned JSON Schema registry for canonical Phase 0 contracts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ell.domain.models import (
    AuditEvent,
    CandidateMemory,
    Episode,
    EvidencePacket,
    ExperienceEvent,
    MemoryRecord,
    RetrievalRequest,
    SourceArtifact,
)

SCHEMA_VERSION = 1

_SCHEMAS: dict[str, type[BaseModel]] = {
    "audit-event": AuditEvent,
    "candidate-memory": CandidateMemory,
    "episode": Episode,
    "evidence-packet": EvidencePacket,
    "experience-event": ExperienceEvent,
    "memory-record": MemoryRecord,
    "retrieval-request": RetrievalRequest,
    "source-artifact": SourceArtifact,
}


def schema_id(name: str, version: int = SCHEMA_VERSION) -> str:
    """Return the stable, technology-neutral identifier for a contract."""
    if version != SCHEMA_VERSION:
        raise KeyError(f"unsupported schema version: {version}")
    if name not in _SCHEMAS:
        raise KeyError(f"unknown schema: {name}")
    return f"https://l.local/schemas/domain/{name}.v{version}.json"


def json_schema(name: str, version: int = SCHEMA_VERSION) -> dict[str, Any]:
    """Generate a versioned JSON Schema from the canonical Pydantic boundary."""
    identifier = schema_id(name, version)
    schema = _SCHEMAS[name].model_json_schema(mode="validation")
    return {"$id": identifier, "$schema": "https://json-schema.org/draft/2020-12/schema", **schema}


def schema_catalog(version: int = SCHEMA_VERSION) -> dict[str, dict[str, Any]]:
    """Return every canonical schema for an export or contract test."""
    return {name: json_schema(name, version) for name in sorted(_SCHEMAS)}
