"""Frozen paired analysis helpers for the preregistered benchmark."""

from __future__ import annotations

import math
import random
from typing import Iterable, List, Sequence, Tuple


def paired_difference(left: Sequence[bool], right: Sequence[bool]) -> float:
    """Return left-minus-right success in percentage-point units."""
    if len(left) != len(right) or not left:
        raise ValueError("paired samples must have the same non-zero length")
    return sum(int(a) - int(b) for a, b in zip(left, right)) / len(left)


def paired_bootstrap_interval(
    left: Sequence[bool],
    right: Sequence[bool],
    *,
    seed: int,
    iterations: int = 10_000,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    """Compute the frozen percentile interval over paired task indices."""
    if len(left) != len(right) or not left:
        raise ValueError("paired samples must have the same non-zero length")
    rng = random.Random(seed)
    differences: List[float] = []
    for _ in range(iterations):
        indices = [rng.randrange(len(left)) for _ in range(len(left))]
        differences.append(
            sum(int(left[index]) - int(right[index]) for index in indices) / len(indices)
        )
    differences.sort()
    lower = differences[math.floor((alpha / 2) * (iterations - 1))]
    upper = differences[math.ceil((1 - alpha / 2) * (iterations - 1))]
    return lower, upper


def minimum_paired_sample_size(
    *, effect: float = 0.05, discordance: float = 0.20, alpha_z: float = 1.96, power_z: float = 0.84
) -> int:
    """Approximate paired-binary sample size under the frozen Phase 0 assumptions."""
    if not 0 < effect < discordance < 1:
        raise ValueError("require 0 < effect < discordance < 1")
    numerator = alpha_z * math.sqrt(discordance) + power_z * math.sqrt(
        discordance - effect * effect
    )
    return math.ceil((numerator / effect) ** 2)


def mean(values: Iterable[float]) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else 0.0
