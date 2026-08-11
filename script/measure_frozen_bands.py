#!/usr/bin/env python3
"""Measure frozen-scorer null floors and oracle ceilings without eligible policies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, List, Sequence

from ell.benchmark import (
    ELIGIBLE_COMPARATORS,
    NULL_POLICY_CONDITIONS,
    calibrate_null_policy_accuracy,
    generate_development_dataset,
    run_baseline,
)

DEFAULT_SEEDS = (1729, 11, 42, 101, 777, 2026, 31337, 8080)
STRATA = ("near", "intermediate", "far")
ORACLE = "oracle-retrieval"
TARGET_EFFECT = 0.05
QUANTILE = 0.999
SEALED_PLACEHOLDER = "sha256:" + "a" * 64


def _accuracy_by_stratum(dataset: Any, run: Any) -> Dict[str, float]:
    partition = next(item for item in dataset.partitions if item.name == "development")
    transfer = {task.task_id: task.transfer for task in partition.tasks}
    return {
        stratum: mean(
            result.correct
            for result in run.task_results
            if transfer[result.task_id] == stratum
        )
        for stratum in STRATA
    }


def measure(
    *, seeds: Sequence[int], permutations: int, permutation_seed: int, source_commit: str
) -> Dict[str, Any]:
    executed = set(NULL_POLICY_CONDITIONS) | {ORACLE}
    overlap = executed & set(ELIGIBLE_COMPARATORS)
    if overlap:
        raise AssertionError(f"eligible conditions would be executed: {sorted(overlap)}")

    rows: List[Dict[str, Any]] = []
    for seed in seeds:
        dataset = generate_development_dataset(seed, SEALED_PLACEHOLDER)
        calibrations = calibrate_null_policy_accuracy(
            dataset,
            "development",
            permutations=permutations,
            permutation_seed=permutation_seed,
        )
        oracle_run = run_baseline(dataset, "development", ORACLE)
        ceiling = _accuracy_by_stratum(dataset, oracle_run)
        for stratum in STRATA:
            candidates = [item for item in calibrations if item.stratum == stratum]
            floor = max(item.null_q999 for item in candidates)
            floor_policies = sorted(
                item.policy_id for item in candidates if item.null_q999 == floor
            )
            upper = ceiling[stratum] - TARGET_EFFECT
            rows.append(
                {
                    "seed": seed,
                    "stratum": stratum,
                    "floor_q999_exclusive": floor,
                    "floor_policies": floor_policies,
                    "oracle_ceiling": ceiling[stratum],
                    "effect_reserved_upper_inclusive": upper,
                    "corridor": upper - floor,
                    "admissible": floor < upper,
                    "dataset_hash": dataset.dataset_hash,
                    "oracle_result_hash": oracle_run.result_hash,
                }
            )

    summary: Dict[str, Dict[str, float]] = {}
    for stratum in STRATA:
        selected = [row for row in rows if row["stratum"] == stratum]
        ceilings = [row["oracle_ceiling"] for row in selected]
        floors = [row["floor_q999_exclusive"] for row in selected]
        corridors = [row["corridor"] for row in selected]
        summary[stratum] = {
            "ceiling_mean": mean(ceilings),
            "ceiling_population_sd": pstdev(ceilings),
            "floor_mean": mean(floors),
            "floor_worst_seed": max(floors),
            "corridor_min": min(corridors),
        }

    return {
        "measurement": "ell.frozen-instrument-bands.v1",
        "source_commit": source_commit,
        "partition": "development",
        "sealed_generated": False,
        "eligible_conditions_executed": [],
        "conditions_executed": sorted(executed),
        "seeds": list(seeds),
        "permutations_per_seed": permutations,
        "permutation_seed": permutation_seed,
        "quantile": QUANTILE,
        "quantile_rule": "nearest_rank_ceil_probability_times_n_minus_one",
        "target_effect": TARGET_EFFECT,
        "pass_rule": "score > floor_q999_exclusive per seed and stratum",
        "rows": rows,
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--permutations", type=int, default=10_000)
    parser.add_argument("--permutation-seed", type=int, default=90_009)
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS)
    args = parser.parse_args()
    result = measure(
        seeds=args.seeds,
        permutations=args.permutations,
        permutation_seed=args.permutation_seed,
        source_commit=args.source_commit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
