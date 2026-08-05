"""Tests for evidence schemas."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ell.evidence.schemas import EvidenceData


def test_evidence_data_valid() -> None:
    """EvidenceData should accept valid data."""
    data = EvidenceData(
        message_id=uuid4(),
        type="DECISION",
        statement="Focus on reflection engines.",
        subject="Experience Learning Layer",
        temporal_scope="PROJECT",
        importance=0.91,
        extraction_confidence=0.98,
    )

    assert data.type == "DECISION"
    assert data.importance == 0.91


def test_evidence_data_rejects_invalid_importance() -> None:
    """EvidenceData should reject importance outside 0-1."""
    with pytest.raises(ValueError):
        EvidenceData(
            message_id=uuid4(),
            type="FACT",
            statement="test",
            subject="test",
            temporal_scope="ONGOING",
            importance=1.5,
            extraction_confidence=0.5,
        )


def test_evidence_data_rejects_invalid_confidence() -> None:
    """EvidenceData should reject confidence outside 0-1."""
    with pytest.raises(ValueError):
        EvidenceData(
            message_id=uuid4(),
            type="FACT",
            statement="test",
            subject="test",
            temporal_scope="ONGOING",
            importance=0.5,
            extraction_confidence=-0.1,
        )
