"""Canonical serialization, hashing, and deterministic identifiers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


def canonical_value(value: Any) -> Any:
    """Convert supported values into a stable JSON-compatible representation."""
    if hasattr(value, "model_dump"):
        return canonical_value(value.model_dump(mode="json", exclude_none=True))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [canonical_value(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    """Serialize without platform-dependent whitespace or key ordering."""
    return json.dumps(
        canonical_value(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


def sha256_digest(value: Any) -> str:
    """Return a prefixed digest of a canonical value."""
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def content_digest(text: str) -> str:
    """Hash source text exactly as stored."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(kind: str, *parts: Any) -> str:
    """Create a readable deterministic identifier from immutable identity fields."""
    digest = hashlib.sha256(canonical_json([kind, *parts]).encode("utf-8")).hexdigest()
    return f"{kind}_{digest[:24]}"
