"""Local embedding provider via LM Studio."""

from __future__ import annotations

import httpx

from ell.embeddings.base import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):
    """Embedding provider backed by a local LM Studio endpoint."""

    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = "bge-m3"):
        self.base_url = base_url
        self.model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                json={"model": self.model, "input": texts},
            )
            resp.raise_for_status()
            body = resp.json()
            return [item["embedding"] for item in body["data"]]

    async def embed_single(self, text: str) -> list[float]:
        embeddings = await self.embed([text])
        return embeddings[0]
