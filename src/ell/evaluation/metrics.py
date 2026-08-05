"""Evaluation metrics calculation."""

from __future__ import annotations


def precision(predicted: list[str], relevant: list[str]) -> float:
    """Calculate precision: how many predicted are relevant."""
    if not predicted:
        return 0.0
    hits = sum(1 for p in predicted if p in relevant)
    return hits / len(predicted)


def recall(predicted: list[str], relevant: list[str]) -> float:
    """Calculate recall: how many relevant were predicted."""
    if not relevant:
        return 0.0
    hits = sum(1 for p in predicted if p in relevant)
    return hits / len(relevant)


def f1(precision_val: float, recall_val: float) -> float:
    """Calculate F1 score."""
    if precision_val + recall_val == 0:
        return 0.0
    return 2 * (precision_val * recall_val) / (precision_val + recall_val)
