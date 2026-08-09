from __future__ import annotations

import json
from pathlib import Path

from ell.benchmark import (
    BASELINES,
    generate_dataset,
    generate_development_dataset,
    run_baseline,
    write_artifacts,
)


def test_generation_is_byte_stable_for_same_seeds() -> None:
    first = generate_dataset(1729, 481516)
    second = generate_dataset(1729, 481516)
    assert first == second
    assert first.dataset_hash == second.dataset_hash


def test_sealed_seed_changes_sealed_data_and_commitment_only() -> None:
    first = generate_dataset(1729, 481516)
    second = generate_dataset(1729, 481517)
    assert first.partitions[:2] == second.partitions[:2]
    assert first.partitions[2] != second.partitions[2]
    assert first.seed_commitment != second.seed_commitment


def test_development_artifact_does_not_contain_sealed_partition(tmp_path: Path) -> None:
    commitment = "sha256:" + "a" * 64
    dataset = generate_development_dataset(1729, commitment)
    write_artifacts(tmp_path, dataset, "development")
    serialized = json.loads((tmp_path / "dataset.json").read_text())
    assert [item["name"] for item in serialized["partitions"]] == ["train", "development"]
    assert serialized["seed_commitment"] == commitment


def test_partitions_are_chronological_and_identifiers_are_unique() -> None:
    dataset = generate_dataset(1729, 481516)
    assert [len(partition.records) for partition in dataset.partitions] == [50, 200, 1_000]
    assert [len(partition.tasks) for partition in dataset.partitions] == [30, 120, 640]
    prior_max = None
    identifiers = set()
    for partition in dataset.partitions:
        assert [item.observed_time for item in partition.records] == sorted(
            item.observed_time for item in partition.records
        )
        assert [item.observed_time for item in partition.tasks] == sorted(
            item.observed_time for item in partition.tasks
        )
        times = [item.observed_time for item in [*partition.records, *partition.tasks]]
        if prior_max is not None:
            assert min(times) > prior_max
        prior_max = max(times)
        current = {item.record_id for item in partition.records} | {
            item.task_id for item in partition.tasks
        }
        assert not identifiers & current
        identifiers |= current


def test_streams_cover_change_deletion_permissions_delays_and_correlation() -> None:
    dataset = generate_dataset(1729, 481516)
    for partition in dataset.partitions:
        assert any(item.change_point for item in partition.records)
        assert any(item.deleted for item in partition.records)
        assert any(item.permission == "denied" for item in partition.records)
        assert any(item.outcome_observed_time > item.observed_time for item in partition.records)
        groups = [item.correlation_group for item in partition.records if item.correlation_group]
        assert len(groups) > len(set(groups))


def test_every_baseline_emits_complete_reproducible_receipts() -> None:
    dataset = generate_dataset(1729, 481516)
    for baseline_id in BASELINES:
        first = run_baseline(dataset, "development", baseline_id)
        second = run_baseline(dataset, "development", baseline_id)
        assert first.result_hash == second.result_hash
        assert len(first.receipts) == len(first.task_results) == len(first.judgments)
        assert first.manifest.dataset_hash == dataset.dataset_hash
        assert first.manifest.cost.total_tokens == sum(
            result.cost.total_tokens for result in first.task_results
        )


def test_benchmark_distinguishes_no_memory_from_known_good_policy() -> None:
    dataset = generate_dataset(1729, 481516)
    broken = run_baseline(dataset, "development", "no-memory")
    known_good = run_baseline(dataset, "development", "direct-insight")
    assert broken.accuracy == 0.0
    assert known_good.accuracy == 1.0
    assert known_good.accuracy > broken.accuracy


def test_maximum_context_exposes_distractor_cost() -> None:
    dataset = generate_dataset(1729, 481516)
    maximum = run_baseline(dataset, "development", "maximum-context")
    focused = run_baseline(dataset, "development", "direct-insight")
    assert maximum.manifest.cost.total_tokens > focused.manifest.cost.total_tokens
