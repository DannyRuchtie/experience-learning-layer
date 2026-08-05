"""Provider-neutral language model interface."""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelProvider(str, enum.Enum):
    """Supported model providers."""
    LM_STUDIO = "lm_studio"
    OPENAI = "openai"
    FAKE = "fake"


class ModelUsage(BaseModel):
    """Token usage metadata for a model call."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ModelResponse(BaseModel, Generic[T]):
    """Structured response from a language model."""
    data: T
    provider: ModelProvider
    model_name: str
    prompt_version: str
    usage: ModelUsage
    generated_at: datetime = datetime.now(timezone.utc)


class LanguageModel(ABC):
    """Abstract interface for all language model providers."""

    @abstractmethod
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        prompt_version: str = "1.0.0",
    ) -> ModelResponse[T]:
        """Generate a structured response and return it typed as T."""
        ...


class LMStudioClient(LanguageModel):
    """Client for a local LM Studio endpoint."""

    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = "qwen"):
        self.base_url = base_url
        self.model = model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        prompt_version: str = "1.0.0",
    ) -> ModelResponse[T]:
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            body = resp.json()
            text = body["choices"][0]["message"]["content"]

        parsed = response_model.model_validate_json(text or "{}")
        return ModelResponse[T](
            data=parsed,
            provider=ModelProvider.LM_STUDIO,
            model_name=self.model,
            prompt_version=prompt_version,
            usage=ModelUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            ),
        )


class OpenAIClient(LanguageModel):
    """Client for OpenAI-compatible API."""

    def __init__(self, api_key: str = "", model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        prompt_version: str = "1.0.0",
    ) -> ModelResponse[T]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        resp = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        choice = resp.choices[0]
        text = choice.message.content

        parsed = response_model.model_validate_json(text or "{}")
        return ModelResponse[T](
            data=parsed,
            provider=ModelProvider.OPENAI,
            model_name=self.model,
            prompt_version=prompt_version,
            usage=ModelUsage(
                prompt_tokens=(resp.usage.prompt_tokens) if resp.usage else 0,
                completion_tokens=(resp.usage.completion_tokens) if resp.usage else 0,
                total_tokens=(resp.usage.total_tokens) if resp.usage else 0,
            ),
        )


class FakeModelClient(LanguageModel):
    """Deterministic fake client for tests. Returns pre-programmed responses."""

    def __init__(self, responses: dict[str, BaseModel] | None = None):
        self.responses: dict[str, BaseModel] = responses or {}
        self.call_log: list[dict[str, Any]] = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        prompt_version: str = "1.0.0",
    ) -> ModelResponse[T]:
        key = f"{prompt_version}:{user_prompt[:80]}"
        if key in self.responses:
            data = self.responses[key]
        else:
            import inspect
            sig = inspect.signature(response_model.__init__)
            defaults = {}
            for pname, pval in sig.parameters.items():
                if pval.default is not inspect.Parameter.empty:
                    defaults[pname] = pval.default
            data = response_model.model_validate(defaults)

        entry = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "prompt_version": prompt_version,
            "response_model": response_model.__name__,
            "data": data.model_dump(mode="json"),
        }
        self.call_log.append(entry)

        return ModelResponse[T](
            data=data,  # type: ignore
            provider=ModelProvider.FAKE,
            model_name="fake",
            prompt_version=prompt_version,
            usage=ModelUsage(),
        )
