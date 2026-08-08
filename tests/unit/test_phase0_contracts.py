"""Contract tests for schemas, mock provider, identifiers, and golden corpus."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import BaseModel, Field, ValidationError

from ell.domain.identifiers import stable_episode_id, stable_event_id, stable_source_id
from ell.domain.providers import DeterministicMockProvider
from ell.domain.schema_registry import SCHEMA_VERSION, schema_catalog, schema_id
from ell.evaluation.golden import load_golden_cases


class MockClaim(BaseModel):
    """Small structured result used to exercise provider validation."""

    statement: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


def test_schema_catalog_has_stable_versioned_ids() -> None:
    """Every canonical Phase 0 object has an explicit v1 JSON Schema ID."""
    catalog = schema_catalog()
    assert set(catalog) == {
        "audit-event",
        "candidate-memory",
        "episode",
        "evidence-packet",
        "experience-event",
        "memory-record",
        "retrieval-request",
        "source-artifact",
    }
    for name, schema in catalog.items():
        assert schema["$id"] == schema_id(name, SCHEMA_VERSION)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_schema_registry_rejects_unknown_versions() -> None:
    """Schema evolution cannot silently serve another contract as v1."""
    with pytest.raises(KeyError, match="unsupported schema version"):
        schema_catalog(version=2)


def test_deterministic_provider_validates_and_replays_fixture() -> None:
    """The mock returns identical typed data without model or network dependencies."""
    provider = DeterministicMockProvider(
        {"preference": {"statement": "Use Markdown", "confidence": 0.98}}
    )
    first = provider.generate_structured(
        fixture_key="preference",
        response_model=MockClaim,
        prompt_version="pref-v1",
    )
    second = provider.generate_structured(
        fixture_key="preference",
        response_model=MockClaim,
        prompt_version="pref-v1",
    )
    assert first == second
    assert first.data.statement == "Use Markdown"
    assert provider.calls == ["preference", "preference"]
    assert provider.capabilities.local_execution is True


def test_deterministic_provider_fails_on_invalid_or_missing_fixture() -> None:
    """Malformed model output is never silently coerced into a candidate."""
    invalid = DeterministicMockProvider({"bad": {"statement": "Unsupported", "confidence": 2.0}})
    with pytest.raises(ValidationError):
        invalid.generate_structured(
            fixture_key="bad",
            response_model=MockClaim,
            prompt_version="v1",
        )
    with pytest.raises(KeyError, match="no deterministic fixture"):
        invalid.generate_structured(
            fixture_key="missing",
            response_model=MockClaim,
            prompt_version="v1",
        )


def test_source_event_and_episode_ids_are_deterministic() -> None:
    """Rerunning normalization yields identical provider-neutral IDs."""
    workspace_id = uuid4()
    source_a = stable_source_id("chatgpt_export", "conversation-123")
    source_b = stable_source_id("chatgpt_export", "conversation-123")
    event_a = stable_event_id(source_a, "message-456")
    event_b = stable_event_id(source_b, "message-456")
    assert source_a == source_b
    assert event_a == event_b
    assert stable_episode_id(workspace_id, (event_a,)) == stable_episode_id(
        workspace_id, (event_b,)
    )


def test_golden_corpus_is_versioned_unique_and_covers_risk_cases() -> None:
    """The synthetic corpus validates and covers required Phase 0 behaviors."""
    path = Path("evals/golden/v1/cases.jsonl")
    cases = load_golden_cases(path)
    assert len(cases) == 9
    assert len({case.id for case in cases}) == len(cases)
    assert {case.expected.policy_action for case in cases} == {
        "auto_commit",
        "await_review",
        "reject",
    }
    assert any(case.expected.preserves_prior for case in cases)
    assert any(case.expected.returns_contradiction for case in cases)
    assert any("prompt-injection" in case.id for case in cases)
