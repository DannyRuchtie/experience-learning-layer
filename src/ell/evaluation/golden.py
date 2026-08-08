"""Typed loader for the consent-safe synthetic Phase 0 golden corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GoldenEvidence(BaseModel):
    """An exact source span and its expected relation to a candidate claim."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    relation: Literal["supports", "contradicts"]


class GoldenExpectation(BaseModel):
    """Expected deterministic policy and lifecycle behavior."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_action: Literal["auto_commit", "await_review", "reject"]
    memory_type: str
    preserves_prior: bool = False
    returns_contradiction: bool = False


class GoldenCase(BaseModel):
    """One synthetic, non-personal conformance scenario."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^golden-v1-[a-z0-9-]+$")
    description: str
    evidence: tuple[GoldenEvidence, ...]
    candidate: dict[str, object]
    expected: GoldenExpectation


def load_golden_cases(path: Path) -> tuple[GoldenCase, ...]:
    """Load and validate every non-empty JSONL line; malformed data fails loudly."""
    cases: list[GoldenCase] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            case = GoldenCase.model_validate(json.loads(line))
            if case.id in seen:
                raise ValueError(f"duplicate golden case at line {line_number}: {case.id}")
            seen.add(case.id)
            cases.append(case)
    if not cases:
        raise ValueError("golden corpus is empty")
    return tuple(cases)
