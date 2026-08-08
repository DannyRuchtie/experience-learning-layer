"""Provider capability contract and deterministic structured-output mock."""

from __future__ import annotations

from typing import Any, Generic, Protocol, Type, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound=BaseModel)


class ModelCapabilities(BaseModel):
    """Provider-neutral capability and data-handling declaration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    structured_output: bool
    local_execution: bool
    maximum_sensitivity: str
    context_limit: int


class StructuredModelResponse(BaseModel, Generic[T]):
    """Validated structured result with reproducible provider lineage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    data: T
    provider_id: str
    model_id: str
    prompt_version: str


class StructuredModelProvider(Protocol):
    """Minimal model port; no vendor response objects cross this boundary."""

    @property
    def capabilities(self) -> ModelCapabilities:
        """Declare provider capabilities before task routing."""

    def generate_structured(
        self,
        *,
        fixture_key: str,
        response_model: Type[T],
        prompt_version: str,
    ) -> StructuredModelResponse[T]:
        """Generate and validate a response against the requested boundary model."""


class DeterministicMockProvider:
    """Fixture-backed provider that performs no I/O and never guesses a response."""

    def __init__(self, fixtures: dict[str, dict[str, Any]]) -> None:
        self._fixtures = fixtures.copy()
        self.calls: list[str] = []

    @property
    def capabilities(self) -> ModelCapabilities:
        """Declare stable mock capabilities."""
        return ModelCapabilities(
            structured_output=True,
            local_execution=True,
            maximum_sensitivity="restricted",
            context_limit=1_000_000,
        )

    def generate_structured(
        self,
        *,
        fixture_key: str,
        response_model: Type[T],
        prompt_version: str,
    ) -> StructuredModelResponse[T]:
        """Return the named fixture only after schema validation."""
        if fixture_key not in self._fixtures:
            raise KeyError(f"no deterministic fixture: {fixture_key}")
        self.calls.append(fixture_key)
        data = response_model.model_validate(self._fixtures[fixture_key])
        return StructuredModelResponse[T](
            data=data,
            provider_id="deterministic-mock",
            model_id="fixture-v1",
            prompt_version=prompt_version,
        )
