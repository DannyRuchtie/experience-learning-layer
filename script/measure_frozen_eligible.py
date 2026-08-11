#!/usr/bin/env python3
"""Measure eligible comparators after frozen pass marks have been fixed."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, List

from ell.benchmark import (
    ELIGIBLE_COMPARATORS,
    generate_development_dataset,
    run_baseline,
)

SEALED_PLACEHOLDER = "sha256:" + "a" * 64


def measure(*, bands_path: Path, source_commit: str) -> Dict[str, Any]:
    band_bytes = bands_path.read_bytes()
    bands = json.loads(band_bytes)
    if bands["eligible_conditions_executed"]:
        raise ValueError("band artifact was contaminated by eligible conditions")
    if bands["sealed_generated"]:
        raise ValueError("band artifact generated the sealed partition")

    marks = {
        (row["seed"], row["stratum"]): row["floor_q999_exclusive"]
        for row in bands["rows"]
    }
    rows: List[Dict[str, Any]] = []
    rule_rows: List[Dict[str, Any]] = []
    for seed in bands["seeds"]:
        dataset = generate_development_dataset(seed, SEALED_PLACEHOLDER)
        partition = next(item for item in dataset.partitions if item.name == "development")
        tasks = {task.task_id: task for task in partition.tasks}
        for comparator in ELIGIBLE_COMPARATORS:
            run = run_baseline(dataset, "development", comparator)
            for stratum in ("near", "intermediate", "far"):
                results = [
                    result
                    for result in run.task_results
                    if tasks[result.task_id].transfer == stratum
                ]
                accuracy = mean(result.correct for result in results)
                mark = marks[(seed, stratum)]
                rows.append(
                    {
                        "seed": seed,
                        "comparator": comparator,
                        "stratum": stratum,
                        "accuracy": accuracy,
                        "q999_pass_mark_exclusive": mark,
                        "margin_above_mark": accuracy - mark,
                        "passes": accuracy > mark,
                    }
                )

            rule_ids = sorted({task.rule_id for task in partition.tasks})
            result_by_task = {result.task_id: result for result in run.task_results}
            for rule_id in rule_ids:
                far_tasks = [
                    task
                    for task in partition.tasks
                    if task.rule_id == rule_id and task.transfer == "far"
                ]
                rule_rows.append(
                    {
                        "seed": seed,
                        "comparator": comparator,
                        "rule_id": rule_id,
                        "far_accuracy": mean(
                            result_by_task[task.task_id].correct for task in far_tasks
                        ),
                    }
                )

    summary: Dict[str, Dict[str, Any]] = {}
    for comparator in ELIGIBLE_COMPARATORS:
        selected = [row for row in rows if row["comparator"] == comparator]
        far = [row for row in selected if row["stratum"] == "far"]
        far_rules = [
            row["far_accuracy"]
            for row in rule_rows
            if row["comparator"] == comparator
        ]
        summary[comparator] = {
            "far_accuracy_mean": mean(row["accuracy"] for row in far),
            "far_accuracy_population_sd_across_seeds": pstdev(
                row["accuracy"] for row in far
            ),
            "far_rule_accuracy_population_sd": pstdev(far_rules),
            "seed_stratum_passes": sum(row["passes"] for row in selected),
            "seed_stratum_tests": len(selected),
            "far_seed_passes": sum(row["passes"] for row in far),
            "far_seed_tests": len(far),
        }

    return {
        "measurement": "ell.frozen-eligible-development.v1",
        "source_commit": source_commit,
        "band_artifact_sha256": hashlib.sha256(band_bytes).hexdigest(),
        "partition": "development",
        "sealed_generated": False,
        "eligible_conditions_executed": list(ELIGIBLE_COMPARATORS),
        "seeds": bands["seeds"],
        "rows": rows,
        "summary": summary,
        "sizing_warning": (
            "The far-rule SDs are comparator-only descriptive statistics, not the "
            "per-rule paired ELL-minus-comparator SD required by clusters_for_power."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bands", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    result = measure(bands_path=args.bands, source_commit=args.source_commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
