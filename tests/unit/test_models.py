"""Tests for the language model abstraction."""

from __future__ import annotations

import pytest

from ell.models.client import (
    FakeModelClient,
    LanguageModel,
    ModelProvider,
    ModelResponse,
    ModelUsage,
)
from pydantic import BaseModel


class SampleResponse(BaseModel):
    statement: str = "default"
    confidence: float = 0.0


@pytest.mark.asyncio
async def test_fake_model_returns_configured_response() -> None:
    """FakeModelClient should return pre-programmed responses."""
    fake = FakeModelClient()

    sample = SampleResponse(statement="test", confidence=0.9)
    fake.responses["1.0.0:test prompt"] = sample

    resp = await fake.generate_structured(
        system_prompt="test system",
        user_prompt="test prompt",
        response_model=SampleResponse,
        prompt_version="1.0.0",
    )

    assert resp.provider == ModelProvider.FAKE
    assert resp.model_name == "fake"
    assert resp.data.statement == "test"
    assert resp.data.confidence == 0.9
    assert resp.usage == ModelUsage()


@pytest.mark.asyncio
async def test_fake_model_call_log() -> None:
    """FakeModelClient should log all calls."""
    fake = FakeModelClient()

    await fake.generate_structured(
        system_prompt="sys",
        user_prompt="user",
        response_model=SampleResponse,
    )

    assert len(fake.call_log) == 1
    entry = fake.call_log[0]
    assert entry["system_prompt"] == "sys"
    assert entry["user_prompt"] == "user"
    assert entry["response_model"] == "SampleResponse"


def test_language_model_is_abstract() -> None:
    """LanguageModel should not be instantiable directly."""
    with pytest.raises(TypeError):
        LanguageModel()  # type: ignore[abstract]
