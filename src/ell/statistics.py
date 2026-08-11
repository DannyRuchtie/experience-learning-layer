"""Frozen paired analysis and design-sizing helpers for the preregistered benchmark.

Two families of function live here.

*Analysis* helpers (``paired_difference``, ``paired_bootstrap_interval``,
``paired_bca_interval``) compute the statistics the sealed run reports. Their
conventions are pinned so that an independent replication reproduces bounds
exactly rather than approximately.

*Design* helpers (``mcnemar_sample_size``, ``noninferiority_sample_size``,
``conjunctive_power``, ``discordance_sensitivity``) derive the sample size the
contract commits to. Every design assumption is an explicit argument: none of
these functions carries a default discordant-pair rate, because a silent default
is how an unjustified assumption becomes a frozen constant.
"""

from __future__ import annotations

import math
import random
from statistics import NormalDist
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

_NORMAL = NormalDist()

# Percentile-index convention for every bootstrap interval in this project.
# Pinned so replications match bound-for-bound rather than within resampling noise.
BOOTSTRAP_INDEX_CONVENTION = "floor_lower_ceil_upper_over_b_minus_one"


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def paired_difference(left: Sequence[bool], right: Sequence[bool]) -> float:
    """Return left-minus-right success as an absolute proportion difference."""
    if len(left) != len(right) or not left:
        raise ValueError("paired samples must have the same non-zero length")
    return sum(int(a) - int(b) for a, b in zip(left, right)) / len(left)


def discordant_pair_rate(left: Sequence[bool], right: Sequence[bool]) -> float:
    """Return the observed proportion of pairs on which the conditions disagree.

    The design assumptions in the contract are stated in terms of this quantity,
    so the sealed run must report it alongside the primary estimate. A large gap
    between assumed and observed discordance is a reportable deviation.
    """
    if len(left) != len(right) or not left:
        raise ValueError("paired samples must have the same non-zero length")
    return sum(1 for a, b in zip(left, right) if bool(a) != bool(b)) / len(left)


def _resample_differences(
    left: Sequence[bool], right: Sequence[bool], *, seed: int, iterations: int
) -> List[float]:
    rng = random.Random(seed)
    size = len(left)
    differences: List[float] = []
    for _ in range(iterations):
        indices = [rng.randrange(size) for _ in range(size)]
        differences.append(sum(int(left[i]) - int(right[i]) for i in indices) / size)
    differences.sort()
    return differences


def paired_bootstrap_interval(
    left: Sequence[bool],
    right: Sequence[bool],
    *,
    seed: int,
    iterations: int = 10_000,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    """Compute the frozen percentile interval over paired task indices.

    Used for the primary transfer estimate. For the non-inferiority guardrail use
    :func:`paired_bca_interval` instead: the percentile interval is known to
    undercover for differences of proportions at low discordance, and the
    guardrail decision depends on the upper bound rather than on exclusion of
    zero.
    """
    if len(left) != len(right) or not left:
        raise ValueError("paired samples must have the same non-zero length")
    differences = _resample_differences(left, right, seed=seed, iterations=iterations)
    lower = differences[math.floor((alpha / 2) * (iterations - 1))]
    upper = differences[math.ceil((1 - alpha / 2) * (iterations - 1))]
    return lower, upper


def paired_cluster_bootstrap_interval(
    left: Sequence[bool],
    right: Sequence[bool],
    clusters: Sequence[str],
    *,
    seed: int,
    iterations: int = 10_000,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    """Cluster bootstrap over latent-rule identity, resampling clusters not tasks.

    This is the frozen primary interval. Benchmark tasks are *not* independent
    observations: each task is generated from one latent rule, and tasks sharing a
    rule share their gold action, their supporting evidence, and their surface
    templates. Resampling tasks independently treats correlated items as fresh
    information and understates the variance of the paired difference, sometimes
    by a large factor. The effective sample size of the design is governed by the
    number of distinct latent rules, not the number of task instances.

    Resampling whole rules with replacement and recomputing the difference over
    the pooled tasks of the drawn rules gives an interval whose width reflects the
    real unit of generalisation. The task-level interval from
    :func:`paired_bootstrap_interval` is retained only as a sensitivity analysis
    and must be reported as such.
    """
    if not (len(left) == len(right) == len(clusters)) or not left:
        raise ValueError("paired samples and cluster labels must share a non-zero length")
    grouped: Dict[str, List[int]] = {}
    for index, cluster in enumerate(clusters):
        grouped.setdefault(cluster, []).append(index)
    keys = sorted(grouped)
    if len(keys) < 2:
        raise ValueError("cluster bootstrap requires at least two distinct clusters")
    rng = random.Random(seed)
    differences: List[float] = []
    for _ in range(iterations):
        drawn = [keys[rng.randrange(len(keys))] for _ in range(len(keys))]
        indices = [index for key in drawn for index in grouped[key]]
        differences.append(
            sum(int(left[i]) - int(right[i]) for i in indices) / len(indices)
        )
    differences.sort()
    lower = differences[math.floor((alpha / 2) * (iterations - 1))]
    upper = differences[math.ceil((1 - alpha / 2) * (iterations - 1))]
    return lower, upper


def design_effect(
    left: Sequence[bool], right: Sequence[bool], clusters: Sequence[str], *, seed: int
) -> float:
    """Ratio of cluster-bootstrap to task-bootstrap interval width.

    A value near 1.0 means task-level resampling was adequate. Large values
    quantify how much a task-level interval would have overstated the precision
    of the design. Reported with the sealed result so the clustering penalty is
    visible rather than implicit.
    """
    cluster_low, cluster_high = paired_cluster_bootstrap_interval(
        left, right, clusters, seed=seed
    )
    task_low, task_high = paired_bootstrap_interval(left, right, seed=seed)
    task_width = task_high - task_low
    return (cluster_high - cluster_low) / task_width if task_width else float("inf")


def clusters_for_power(
    *, effect: float, between_cluster_sd: float, alpha: float = 0.05, power: float = 0.80
) -> int:
    """Number of latent-rule clusters needed to detect ``effect``.

    Once tasks are nested in rules, adding tasks to an existing rule buys little
    precision; adding rules buys precision. ``between_cluster_sd`` is the standard
    deviation of the per-rule paired difference, which the development partition
    must estimate before the sealed configuration is frozen.
    """
    if between_cluster_sd <= 0:
        raise ValueError("between_cluster_sd must be positive")
    z_alpha = _NORMAL.inv_cdf(1 - alpha / 2)
    z_power = _NORMAL.inv_cdf(power)
    return math.ceil(((z_alpha + z_power) * between_cluster_sd / effect) ** 2)


def paired_bca_interval(
    left: Sequence[bool],
    right: Sequence[bool],
    *,
    seed: int,
    iterations: int = 10_000,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    """Bias-corrected and accelerated interval for the paired difference.

    This is the frozen decision statistic for the unsupported-generalisation
    non-inferiority gate, where the upper bound must fall below the declared
    margin. BCa corrects the median bias and skewness that make the plain
    percentile interval anti-conservative in exactly that regime.
    """
    if len(left) != len(right) or not left:
        raise ValueError("paired samples must have the same non-zero length")
    size = len(left)
    observed = paired_difference(left, right)
    differences = _resample_differences(left, right, seed=seed, iterations=iterations)

    # Bias correction: how much resampled mass sits below the observed estimate.
    below = sum(1 for value in differences if value < observed)
    if below in (0, iterations):
        return paired_bootstrap_interval(
            left, right, seed=seed, iterations=iterations, alpha=alpha
        )
    z0 = _NORMAL.inv_cdf(below / iterations)

    # Acceleration from the jackknife distribution of the paired differences.
    per_pair = [int(a) - int(b) for a, b in zip(left, right)]
    total = sum(per_pair)
    jackknife = [(total - value) / (size - 1) for value in per_pair] if size > 1 else [0.0]
    jack_mean = sum(jackknife) / len(jackknife)
    deviations = [jack_mean - value for value in jackknife]
    numerator = sum(value**3 for value in deviations)
    denominator = 6.0 * (sum(value**2 for value in deviations) ** 1.5)
    acceleration = numerator / denominator if denominator else 0.0

    def adjusted(probability: float) -> float:
        z = _NORMAL.inv_cdf(probability)
        shifted = z0 + (z0 + z) / max(1e-12, 1 - acceleration * (z0 + z))
        return min(max(_NORMAL.cdf(shifted), 1e-9), 1 - 1e-9)

    lower_index = math.floor(adjusted(alpha / 2) * (iterations - 1))
    upper_index = math.ceil(adjusted(1 - alpha / 2) * (iterations - 1))
    return differences[lower_index], differences[min(upper_index, iterations - 1)]


# ---------------------------------------------------------------------------
# Design sizing
# ---------------------------------------------------------------------------


def mcnemar_sample_size(
    *, effect: float, discordance: float, alpha: float = 0.05, power: float = 0.80
) -> int:
    """Paired-binary sample size for detecting ``effect`` against a null of no difference.

    Connor's normal approximation for McNemar's test. ``effect`` and
    ``discordance`` are absolute proportions of the *total* sample.
    """
    if not 0 < effect < discordance < 1:
        raise ValueError("require 0 < effect < discordance < 1")
    z_alpha = _NORMAL.inv_cdf(1 - alpha / 2)
    z_power = _NORMAL.inv_cdf(power)
    numerator = z_alpha * math.sqrt(discordance) + z_power * math.sqrt(
        discordance - effect * effect
    )
    return math.ceil((numerator / effect) ** 2)


# Retained under the historical name used by the v0.6 contract so that older
# run manifests remain interpretable. New code should call mcnemar_sample_size.
def minimum_paired_sample_size(
    *, effect: float, discordance: float, alpha: float = 0.05, power: float = 0.80
) -> int:
    """Deprecated alias for :func:`mcnemar_sample_size`."""
    return mcnemar_sample_size(effect=effect, discordance=discordance, alpha=alpha, power=power)


def noninferiority_sample_size(
    *,
    margin: float,
    discordance: float,
    true_difference: float = 0.0,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """Paired sample size for a one-sided non-inferiority claim on a proportion difference.

    The gate asserts that the upper confidence bound of the paired difference
    falls below ``margin``. The standard error of that difference is
    approximately ``sqrt(discordance / n)``, so the requirement is

        (z_alpha + z_power) * sqrt(discordance / n) <= margin - true_difference

    Setting ``power`` to 0.5 recovers the weaker "the interval is narrow enough
    to be capable of clearing the margin" requirement, which is what a design
    that ignores power implicitly assumes.
    """
    if not 0 < margin < 1:
        raise ValueError("margin must lie in (0, 1)")
    if not 0 < discordance < 1:
        raise ValueError("discordance must lie in (0, 1)")
    slack = margin - true_difference
    if slack <= 0:
        raise ValueError("true_difference must be strictly below the margin")
    z_alpha = _NORMAL.inv_cdf(1 - alpha / 2)
    z_power = _NORMAL.inv_cdf(power)
    return math.ceil(discordance * ((z_alpha + z_power) / slack) ** 2)


def proportion_lower_bound_sample_size(
    *, threshold: float, assumed_value: float, alpha: float = 0.05, power: float = 0.80
) -> int:
    """Sample size so a proportion's lower confidence bound clears ``threshold``.

    Used for the evidence-quality gates, which are absolute thresholds on
    support precision and counterevidence recall. Stating them as point
    estimates lets sampling noise decide the verdict; stating them as lower
    bounds requires this many adjudicated units.
    """
    if not 0 < threshold < assumed_value < 1:
        raise ValueError("require 0 < threshold < assumed_value < 1")
    z_alpha = _NORMAL.inv_cdf(1 - alpha / 2)
    z_power = _NORMAL.inv_cdf(power)
    variance = assumed_value * (1 - assumed_value)
    return math.ceil(variance * ((z_alpha + z_power) / (assumed_value - threshold)) ** 2)


def conjunctive_power(per_gate_power: Mapping[str, float]) -> float:
    """Probability that every mandatory gate passes, assuming gate independence.

    Independence is an approximation, and a conservative one in the direction
    that matters: correlated gates raise the joint pass probability, so this is a
    lower bound on the chance of a supported verdict. The point of reporting it
    is that a design with seven gates at 0.80 power each has roughly a one-in-five
    chance of certifying a system that is in fact correct.
    """
    product = 1.0
    for value in per_gate_power.values():
        if not 0 < value <= 1:
            raise ValueError("each per-gate power must lie in (0, 1]")
        product *= value
    return product


def per_gate_power_for_target(*, gates: int, target: float) -> float:
    """Minimum per-gate power needed to reach a joint ``target`` across ``gates``."""
    if gates < 1:
        raise ValueError("gates must be at least 1")
    if not 0 < target < 1:
        raise ValueError("target must lie in (0, 1)")
    return float(target ** (1.0 / gates))


def discordance_sensitivity(
    *, effect: float, rates: Sequence[float], alpha: float = 0.05, power: float = 0.80
) -> Dict[float, int]:
    """Required N across candidate discordant-pair rates.

    The contract reports this table rather than a single N so that a reader can
    see how much of the design rests on the assumed rate.
    """
    return {
        rate: mcnemar_sample_size(effect=effect, discordance=rate, alpha=alpha, power=power)
        for rate in rates
    }


def achieved_power(
    *, sample_size: int, effect: float, discordance: float, alpha: float = 0.05
) -> float:
    """Power of McNemar's test at a given N, for reporting realised design strength."""
    if not 0 < effect < discordance < 1:
        raise ValueError("require 0 < effect < discordance < 1")
    z_alpha = _NORMAL.inv_cdf(1 - alpha / 2)
    numerator = effect * math.sqrt(sample_size) - z_alpha * math.sqrt(discordance)
    denominator = math.sqrt(max(discordance - effect * effect, 1e-12))
    return _NORMAL.cdf(numerator / denominator)


def mean(values: Iterable[float]) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else 0.0
