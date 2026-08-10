"""Phase 5 canonical substrate and rebuildable projection conformance tools."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Sequence, Tuple, cast

from pydantic import BaseModel, ConfigDict, Field

from ell.identifiers import canonical_json, sha256_digest


class SubstrateError(ValueError):
    """Base error for canonical substrate contract violations."""


class CanonicalCollisionError(SubstrateError):
    """An immutable identity was reused with different content."""


Payload = Dict[str, object]


class Substrate(Protocol):
    name: str

    def put(self, workspace_id: str, kind: str, object_id: str, payload: Payload) -> str: ...

    def get(self, workspace_id: str, kind: str, object_id: str) -> Optional[Payload]: ...

    def list_ids(self, workspace_id: str, kind: str) -> List[str]: ...

    def tombstone(self, workspace_id: str, kind: str, object_id: str) -> bool: ...

    def close(self) -> None: ...


@dataclass
class InMemorySubstrate:
    """Reference canonical substrate used as the semantic oracle."""

    name: str = "in-memory"
    _rows: Dict[Tuple[str, str, str], Tuple[str, Optional[Payload]]] = field(default_factory=dict)

    def put(self, workspace_id: str, kind: str, object_id: str, payload: Payload) -> str:
        digest = sha256_digest(payload)
        key = (workspace_id, kind, object_id)
        prior = self._rows.get(key)
        if prior is not None:
            if prior[0] != digest:
                raise CanonicalCollisionError(object_id)
            return digest
        self._rows[key] = (digest, json.loads(canonical_json(payload)))
        return digest

    def get(self, workspace_id: str, kind: str, object_id: str) -> Optional[Payload]:
        row = self._rows.get((workspace_id, kind, object_id))
        if row is None or row[1] is None:
            return None
        return cast(Payload, json.loads(canonical_json(row[1])))

    def list_ids(self, workspace_id: str, kind: str) -> List[str]:
        return sorted(
            object_id
            for (workspace, row_kind, object_id), (_, payload) in self._rows.items()
            if workspace == workspace_id and row_kind == kind and payload is not None
        )

    def tombstone(self, workspace_id: str, kind: str, object_id: str) -> bool:
        key = (workspace_id, kind, object_id)
        prior = self._rows.get(key)
        if prior is None:
            return False
        self._rows[key] = (prior[0], None)
        return True

    def close(self) -> None:
        return None


class SQLiteSubstrate:
    """Durable local adapter preserving the same immutable canonical semantics."""

    name = "sqlite"

    def __init__(self, path: Path) -> None:
        self._connection = sqlite3.connect(str(path))
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS canonical_objects (
                workspace_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                object_id TEXT NOT NULL,
                payload_json TEXT,
                payload_hash TEXT NOT NULL,
                tombstoned INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (workspace_id, kind, object_id)
            )
            """
        )
        self._connection.commit()

    def put(self, workspace_id: str, kind: str, object_id: str, payload: Payload) -> str:
        serialized = canonical_json(payload)
        digest = sha256_digest(payload)
        row = self._connection.execute(
            """
            SELECT payload_hash FROM canonical_objects
            WHERE workspace_id=? AND kind=? AND object_id=?
            """,
            (workspace_id, kind, object_id),
        ).fetchone()
        if row is not None:
            if row[0] != digest:
                raise CanonicalCollisionError(object_id)
            return digest
        self._connection.execute(
            """
            INSERT INTO canonical_objects
            (workspace_id, kind, object_id, payload_json, payload_hash, tombstoned)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (workspace_id, kind, object_id, serialized, digest),
        )
        self._connection.commit()
        return digest

    def get(self, workspace_id: str, kind: str, object_id: str) -> Optional[Payload]:
        row = self._connection.execute(
            """
            SELECT payload_json, tombstoned FROM canonical_objects
            WHERE workspace_id=? AND kind=? AND object_id=?
            """,
            (workspace_id, kind, object_id),
        ).fetchone()
        if row is None or row[1] or row[0] is None:
            return None
        value = json.loads(row[0])
        if not isinstance(value, dict):
            raise SubstrateError("canonical payload is not an object")
        return cast(Payload, value)

    def list_ids(self, workspace_id: str, kind: str) -> List[str]:
        rows = self._connection.execute(
            """
            SELECT object_id FROM canonical_objects
            WHERE workspace_id=? AND kind=? AND tombstoned=0
            ORDER BY object_id
            """,
            (workspace_id, kind),
        ).fetchall()
        return [str(row[0]) for row in rows]

    def tombstone(self, workspace_id: str, kind: str, object_id: str) -> bool:
        cursor = self._connection.execute(
            """
            UPDATE canonical_objects
            SET payload_json=NULL, tombstoned=1
            WHERE workspace_id=? AND kind=? AND object_id=?
            """,
            (workspace_id, kind, object_id),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        self._connection.close()


class ProjectionDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_id: str
    workspace_id: str
    text: str
    source_ids: List[str] = Field(min_length=1)


class Projection(Protocol):
    name: str

    def rebuild(self, documents: Sequence[ProjectionDocument]) -> None: ...

    def query(self, workspace_id: str, text: str, limit: int) -> List[str]: ...

    def invalidate_source(self, source_id: str) -> List[str]: ...


@dataclass
class LexicalProjection:
    """Deterministic lexical projection; never a canonical authority."""

    name: str = "lexical"
    _documents: Dict[str, ProjectionDocument] = field(default_factory=dict)

    def rebuild(self, documents: Sequence[ProjectionDocument]) -> None:
        self._documents = {item.document_id: item for item in documents}

    def query(self, workspace_id: str, text: str, limit: int) -> List[str]:
        query = set(_tokens(text))
        ranked = []
        for document in self._documents.values():
            if document.workspace_id != workspace_id:
                continue
            terms = set(_tokens(document.text))
            score = len(query & terms) / max(len(query), 1)
            if score:
                ranked.append((score, document.document_id))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [document_id for _, document_id in ranked[:limit]]

    def invalidate_source(self, source_id: str) -> List[str]:
        removed = sorted(
            document_id
            for document_id, document in self._documents.items()
            if source_id in document.source_ids
        )
        for document_id in removed:
            del self._documents[document_id]
        return removed


@dataclass
class ExactVectorProjection:
    """Exact deterministic character-trigram projection for substrate comparisons."""

    name: str = "exact-vector"
    _documents: Dict[str, ProjectionDocument] = field(default_factory=dict)
    _vectors: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def rebuild(self, documents: Sequence[ProjectionDocument]) -> None:
        self._documents = {item.document_id: item for item in documents}
        self._vectors = {item.document_id: _vector(item.text) for item in documents}

    def query(self, workspace_id: str, text: str, limit: int) -> List[str]:
        query = _vector(text)
        ranked = []
        for document_id, vector in self._vectors.items():
            document = self._documents[document_id]
            if document.workspace_id != workspace_id:
                continue
            score = _cosine(query, vector)
            if score:
                ranked.append((score, document_id))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [document_id for _, document_id in ranked[:limit]]

    def invalidate_source(self, source_id: str) -> List[str]:
        removed = sorted(
            document_id
            for document_id, document in self._documents.items()
            if source_id in document.source_ids
        )
        for document_id in removed:
            del self._documents[document_id]
            del self._vectors[document_id]
        return removed


class AdapterCapability(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    adapter_id: str
    available: bool
    canonical_writes_allowed: bool = False
    role: str = "candidate_retrieval_only"
    reason: str


OPTIONAL_ADAPTERS = {
    "turbovec": AdapterCapability(
        adapter_id="turbovec",
        available=False,
        reason="runtime adapter and frozen version not installed",
    ),
    "tencentdb-agent-memory": AdapterCapability(
        adapter_id="tencentdb-agent-memory",
        available=False,
        reason="external service and licensed frozen fixture not configured",
    ),
}


class ConformanceReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    substrate: str
    checks: Dict[str, bool]

    @property
    def passed(self) -> bool:
        return all(self.checks.values())


def run_substrate_conformance(substrate: Substrate) -> ConformanceReport:
    """Prove identity, isolation, idempotency, collision, and deletion semantics."""
    checks: Dict[str, bool] = {}
    payload = {"value": "portable Markdown", "version": 1}
    digest = substrate.put("workspace-a", "concept", "concept-1", payload)
    checks["round_trip"] = substrate.get("workspace-a", "concept", "concept-1") == payload
    checks["deterministic_hash"] = digest == sha256_digest(payload)
    checks["idempotent_retry"] = (
        substrate.put("workspace-a", "concept", "concept-1", payload) == digest
    )
    substrate.put("workspace-b", "concept", "concept-1", {"value": "isolated"})
    checks["workspace_isolation"] = substrate.get(
        "workspace-a", "concept", "concept-1"
    ) == payload and substrate.get("workspace-b", "concept", "concept-1") == {"value": "isolated"}
    try:
        substrate.put("workspace-a", "concept", "concept-1", {"value": "mutation"})
        checks["collision_rejected"] = False
    except CanonicalCollisionError:
        checks["collision_rejected"] = True
    checks["ordered_listing"] = substrate.list_ids("workspace-a", "concept") == ["concept-1"]
    checks["tombstone_applied"] = substrate.tombstone("workspace-a", "concept", "concept-1")
    checks["deleted_unreachable"] = (
        substrate.get("workspace-a", "concept", "concept-1") is None
        and substrate.list_ids("workspace-a", "concept") == []
    )
    return ConformanceReport(substrate=substrate.name, checks=checks)


def run_projection_conformance(projection: Projection) -> Dict[str, bool]:
    """Verify rebuildability, isolation, stable ranking, and deletion invalidation."""
    documents = [
        ProjectionDocument(
            document_id="doc-a",
            workspace_id="workspace-a",
            text="early stakeholder review for launch",
            source_ids=["source-a"],
        ),
        ProjectionDocument(
            document_id="doc-b",
            workspace_id="workspace-b",
            text="early stakeholder review for launch",
            source_ids=["source-b"],
        ),
    ]
    projection.rebuild(documents)
    first = projection.query("workspace-a", "stakeholder review launch", 5)
    projection.rebuild(documents)
    second = projection.query("workspace-a", "stakeholder review launch", 5)
    removed = projection.invalidate_source("source-a")
    after = projection.query("workspace-a", "stakeholder review launch", 5)
    other = projection.query("workspace-b", "stakeholder review launch", 5)
    return {
        "stable_rebuild": first == second == ["doc-a"],
        "workspace_isolation": "doc-b" not in first,
        "deletion_invalidation": removed == ["doc-a"] and after == [],
        "other_workspace_preserved": other == ["doc-b"],
    }


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _vector(text: str) -> Dict[str, float]:
    normalized = " ".join(_tokens(text))
    return dict(Counter(normalized[index : index + 3] for index in range(len(normalized) - 2)))


def _cosine(left: Dict[str, float], right: Dict[str, float]) -> float:
    numerator = sum(value * right.get(key, 0.0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0
