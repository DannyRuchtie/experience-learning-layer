"""Tests for the health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


def test_health_returns_200() -> None:
    """Health endpoint should return 200 with status ok."""
    client = TestClient(app)
    result = client.get("/health")

    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "ok"
