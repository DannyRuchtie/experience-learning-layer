"""Embedding provider abstraction."""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Interface for embedding providers."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        ...

    @abstractmethod
    async def embed_single(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        ...
