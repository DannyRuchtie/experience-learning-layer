from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from itertools import permutations
from pathlib import Path

import pytest

from ell.benchmark import (
    BASELINES,
    DEVELOPMENT_TIER,
    ELIGIBLE_COMPARATORS,
    SEALED_TIER,
    TRAIN_TIER,
    ExperienceRecord,
    PolicyRecord,
    PolicySelection,
    PolicyTask,
    TaskCase,
    _predict,
    _validate_selections,
    generate_dataset,
    generate_development_dataset,
    project_policy_records,
    project_policy_task,
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
    assert [len(partition.records) for partition in dataset.partitions] == [
        TRAIN_TIER[1],
        DEVELOPMENT_TIER[1],
        SEALED_TIER[1],
    ]
    assert [len(partition.tasks) for partition in dataset.partitions] == [
        TRAIN_TIER[2],
        DEVELOPMENT_TIER[2],
        SEALED_TIER[2],
    ]
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
        assert {item.workspace_id for item in partition.records} == {
            "workspace-alpha",
            "workspace-beta",
        }
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


def test_oracle_concept_uses_the_shared_answer_stage() -> None:
    dataset = generate_dataset(1729, 481516)
    broken = run_baseline(dataset, "development", "no-memory")
    ceiling = run_baseline(dataset, "development", "oracle-concept")
    assert broken.accuracy == 0.0
    assert ceiling.accuracy > broken.accuracy


def test_maximum_context_exposes_distractor_cost() -> None:
    dataset = generate_dataset(1729, 481516)
    maximum = run_baseline(dataset, "development", "maximum-context")
    focused = run_baseline(dataset, "development", "direct-insight")
    assert maximum.manifest.cost.total_tokens > focused.manifest.cost.total_tokens


def test_position_leaking_rolling_summary_is_suspended_from_eligibility() -> None:
    assert "rolling-summary" in BASELINES
    assert "rolling-summary" not in ELIGIBLE_COMPARATORS


def test_development_difficulty_ladder_is_monotonic_without_opening_sealed_data() -> None:
    dataset = generate_development_dataset(1729, "sha256:" + "a" * 64)
    partition = dataset.partitions[-1]
    transfer_by_task = {task.task_id: task.transfer for task in partition.tasks}
    run = run_baseline(dataset, "development", "bm25")
    grouped = {
        stratum: [
            result.correct
            for result in run.task_results
            if transfer_by_task[result.task_id] == stratum
        ]
        for stratum in ("near", "intermediate", "far")
    }
    rates = {name: sum(values) / len(values) for name, values in grouped.items()}
    assert rates["near"] > rates["intermediate"] > rates["far"]


def test_policy_projection_removes_gold_and_enforces_runner_boundaries() -> None:
    decision_time = datetime(2026, 1, 2, tzinfo=timezone.utc)
    task = TaskCase(
        task_id="task-1",
        workspace_id="workspace-alpha",
        rule_id="latent-rule",
        sequence=10,
        observed_time=decision_time,
        query="What should happen?",
        scope="latent-rule",
        transfer="far",
        allowed_actions=["act", "abstain"],
        gold_action="act",
        gold_evidence_ids=["available", "delayed-outcome"],
        gold_counterevidence_ids=[],
    )

    def record(
        record_id: str,
        *,
        sequence: int = 1,
        workspace_id: str = "workspace-alpha",
        permission: str = "benchmark",
        deleted: bool = False,
        outcome_delay_days: int = 0,
    ) -> ExperienceRecord:
        observed_time = decision_time - timedelta(days=1)
        return ExperienceRecord(
            record_id=record_id,
            workspace_id=workspace_id,
            rule_id="latent-rule",
            sequence=sequence,
            observed_time=observed_time,
            text=f"evidence {record_id}",
            scope="latent-rule",
            action="act",
            outcome=1.0,
            outcome_observed_time=observed_time + timedelta(days=outcome_delay_days),
            relation="supports",
            permission=permission,
            deleted=deleted,
        )

    records = [
        record("available"),
        record("delayed-outcome", outcome_delay_days=3),
        record("future-record", sequence=11),
        record("foreign", workspace_id="workspace-beta"),
        record("denied", permission="denied"),
        record("deleted", deleted=True),
    ]
    policy_task = project_policy_task(task)
    visible = project_policy_records(task, records)

    assert set(type(policy_task).model_fields) == {
        "task_id",
        "workspace_id",
        "sequence",
        "observed_time",
        "query",
        "allowed_actions",
    }
    assert [item.record_id for item in visible] == ["available", "delayed-outcome"]
    assert visible[0].observed_outcome == 1.0
    assert visible[1].observed_outcome is None


def test_runner_rejects_policy_selection_outside_issued_context() -> None:
    with pytest.raises(ValueError, match="outside runner context"):
        _validate_selections(
            [PolicySelection(record_id="future", score=1.0)],
            {},
        )


def test_score_aware_decision_uses_pending_outcomes_only_as_tiebreaks() -> None:
    observed_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = {
        "strong": PolicyRecord(
            record_id="strong",
            workspace_id="workspace-alpha",
            sequence=1,
            observed_time=observed_time,
            text="strong evidence",
            observed_action="preferred",
            observed_outcome=1.0,
        ),
        "weak-a": PolicyRecord(
            record_id="weak-a",
            workspace_id="workspace-alpha",
            sequence=2,
            observed_time=observed_time,
            text="observed exception evidence",
            observed_action="other",
            observed_outcome=1.0,
        ),
        "weak-b": PolicyRecord(
            record_id="weak-b",
            workspace_id="workspace-alpha",
            sequence=3,
            observed_time=observed_time,
            text="exception evidence",
            observed_action="other",
            observed_outcome=None,
        ),
    }
    selections = [
        PolicySelection(record_id="strong", score=3.0),
        PolicySelection(record_id="weak-a", score=1.0),
        PolicySelection(record_id="weak-b", score=1.0),
    ]
    task = PolicyTask(
        task_id="task",
        workspace_id="workspace-alpha",
        sequence=4,
        observed_time=observed_time,
        query="What should happen?",
        allowed_actions=["preferred", "other", "abstain"],
    )
    assert {
        _predict(task, list(ordering), records)
        for ordering in permutations(selections)
    } == {"preferred"}

    pending_only = [PolicySelection(record_id="weak-b", score=1.0)]
    assert _predict(task, pending_only, records) == "other"

    exception_first = [
        PolicySelection(record_id="weak-a", score=10.0),
        PolicySelection(record_id="strong", score=1.0),
    ]
    assert _predict(task, exception_first, records) == "other"
