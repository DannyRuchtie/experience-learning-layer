"""Tests for evaluation metrics."""

from __future__ import annotations

from ell.evaluation.metrics import f1, precision, recall


def test_precision_all_hits() -> None:
    """Precision should be 1.0 when all predicted are relevant."""
    assert precision(["a", "b"], ["a", "b"]) == 1.0


def test_precision_no_hits() -> None:
    """Precision should be 0.0 when no predicted are relevant."""
    assert precision(["a", "b"], ["c", "d"]) == 0.0


def test_precision_empty_predicted() -> None:
    """Precision should be 0.0 when predicted is empty."""
    assert precision([], ["a", "b"]) == 0.0


def test_recall_all_hits() -> None:
    """Recall should be 1.0 when all relevant are predicted."""
    assert recall(["a", "b"], ["a", "b"]) == 1.0


def test_recall_partial() -> None:
    """Recall should reflect partial overlap."""
    assert recall(["a"], ["a", "b"]) == 0.5


def test_recall_empty_relevant() -> None:
    """Recall should be 0.0 when relevant is empty."""
    assert recall(["a"], []) == 0.0


def test_f1_perfect() -> None:
    """F1 should be 1.0 when precision and recall are perfect."""
    assert f1(1.0, 1.0) == 1.0


def test_f1_zero() -> None:
    """F1 should be 0.0 when precision and recall are zero."""
    assert f1(0.0, 0.0) == 0.0


def test_f1_balanced() -> None:
    """F1 should be the harmonic mean."""
    assert f1(0.5, 0.5) == 0.5
