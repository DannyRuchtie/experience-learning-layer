from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from itertools import permutations
from pathlib import Path
from statistics import pstdev

import pytest

from ell.benchmark import (
    BASELINES,
    DEVELOPMENT_TIER,
    ELIGIBLE_COMPARATORS,
    NULL_POLICY_CONDITIONS,
    SEALED_TIER,
    TRAIN_TIER,
    BenchmarkDataset,
    ExperienceRecord,
    PolicyRecord,
    PolicySelection,
    PolicyTask,
    TaskCase,
    _oracle_select,
    _predict,
    _validate_selections,
    build_latent_rules,
    calibrate_null_policy_accuracy,
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


def test_action_namespace_is_shared_balanced_and_seed_committed() -> None:
    first = build_latent_rules(24, 1729)
    repeated = build_latent_rules(24, 1729)
    different_seed = build_latent_rules(24, 1730)
    assert first == repeated
    assert [item.preferred_action for item in first] != [
        item.preferred_action for item in different_seed
    ]
    assert {item.preferred_action for item in first} == {"option_a", "option_b"}
    assert sum(item.preferred_action == "option_a" for item in first) == 12
    assert all(
        {item.preferred_action, item.rejected_action} == {"option_a", "option_b"}
        for item in first
    )
    dataset = generate_dataset(1729, 481516)
    for partition in dataset.partitions:
        actions = Counter(
            item.action
            for item in partition.records
            if item.workspace_id == "workspace-alpha"
        )
        assert actions["option_a"] == actions["option_b"]


def test_sealed_seed_changes_sealed_data_and_commitment_only() -> None:
    first = generate_dataset(1729, 481516)
    second = generate_dataset(1729, 481517)
    assert first.partitions[:2] == second.partitions[:2]
    assert first.partitions[2] != second.partitions[2]
    assert first.seed_commitment != second.seed_commitment


def _structural_statistics(
    dataset: BenchmarkDataset, partition_name: str
) -> tuple[float, ...]:
    partition = next(
        item for item in dataset.partitions if item.name == partition_name
    )
    benchmark_records = [
        item for item in partition.records if item.workspace_id == "workspace-alpha"
    ]
    total = len(benchmark_records)
    exceptions = sum(item.relation == "exception" for item in benchmark_records) / total
    contradictions = (
        sum(item.relation == "contradicts" for item in benchmark_records) / total
    )
    change_fraction = sum(item.regime == 0 for item in benchmark_records) / total
    far_sequence_mean = sum(
        item.sequence for item in partition.tasks if item.transfer == "far"
    ) / sum(item.transfer == "far" for item in partition.tasks)
    return exceptions, contradictions, change_fraction, far_sequence_mean


def test_open_generator_seeds_vary_key_structural_statistics() -> None:
    summaries = [
        _structural_statistics(
            generate_development_dataset(seed, "sha256:" + "a" * 64),
            "development",
        )
        for seed in (11, 42, 101, 777)
    ]
    assert all(pstdev(values) > 0 for values in zip(*summaries))


def test_sealed_seed_commits_independent_structural_draw() -> None:
    first = generate_dataset(1729, 481516)
    second = generate_dataset(1729, 481517)
    assert _structural_statistics(first, "sealed") != _structural_statistics(
        second, "sealed"
    )
    assert _structural_statistics(first, "development") == _structural_statistics(
        second, "development"
    )


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


def test_oracle_ranks_gold_evidence_by_policy_visible_recency() -> None:
    dataset = generate_development_dataset(1729, "sha256:" + "a" * 64)
    partition = dataset.partitions[-1]
    task = partition.tasks[0]
    visible = project_policy_records(task, partition.records)
    records_by_id = {item.record_id: item for item in visible}
    selected = _oracle_select(task, visible, "oracle-retrieval")

    assert selected
    assert [records_by_id[item.record_id].sequence for item in selected] == sorted(
        (records_by_id[item.record_id].sequence for item in selected), reverse=True
    )


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


def test_recent_tail_rule_concentration_is_at_chance_for_every_tier() -> None:
    dataset = generate_dataset(1729, 481516)
    assertions = {item.partition: item for item in dataset.positional_leak_assertions}
    assert assertions["sealed"].passed
    assert assertions["sealed"].observed_rate == assertions["sealed"].chance_rate
    for partition in (item for item in dataset.partitions if item.name != "sealed"):
        source_by_id = {item.record_id: item for item in partition.records}
        event_sequences = [item.sequence for item in partition.records] + [
            item.sequence for item in partition.tasks
        ]
        assert len(event_sequences) == len(set(event_sequences))
        matches = 0
        issued = 0
        for task in partition.tasks:
            evidence = task.gold_evidence_ids + task.gold_counterevidence_ids
            assert all(source_by_id[item_id].sequence < task.sequence for item_id in evidence)
            visible = project_policy_records(task, partition.records)
            recent = sorted(visible, key=lambda item: item.sequence, reverse=True)[:5]
            matches += sum(
                source_by_id[item.record_id].rule_id == task.rule_id for item in recent
            )
            issued += len(recent)
        rule_count = len({task.rule_id for task in partition.tasks})
        chance = 1 / rule_count
        standard_error = math.sqrt(chance * (1 - chance) / issued)
        assert matches / issued <= chance + 3 * standard_error
        assertion = assertions[partition.name]
        assert assertion.same_rule_recent_records == matches
        assert assertion.issued_recent_records == issued
        assert assertion.passed


def test_null_policy_selection_precision_is_at_chance_on_open_partitions() -> None:
    dataset = generate_development_dataset(1729, "sha256:" + "a" * 64)
    for partition in dataset.partitions:
        task_by_id = {task.task_id: task for task in partition.tasks}
        record_by_id = {record.record_id: record for record in partition.records}
        rule_count = len({task.rule_id for task in partition.tasks})
        bound = 2 / rule_count
        for baseline_id in NULL_POLICY_CONDITIONS:
            run = run_baseline(dataset, partition.name, baseline_id)
            for stratum in ("near", "intermediate", "far"):
                matches = 0
                selected = 0
                for result in run.task_results:
                    task = task_by_id[result.task_id]
                    if task.transfer != stratum:
                        continue
                    matches += sum(
                        record_by_id[item_id].rule_id == task.rule_id
                        for item_id in result.selected_record_ids
                    )
                    selected += len(result.selected_record_ids)
                assert matches / selected <= bound


def test_null_policy_accuracy_uses_fixed_output_cluster_permutations() -> None:
    dataset = generate_development_dataset(1729, "sha256:" + "a" * 64)
    first = calibrate_null_policy_accuracy(
        dataset, "development", permutations=200, permutation_seed=90_009
    )
    repeated = calibrate_null_policy_accuracy(
        dataset, "development", permutations=200, permutation_seed=90_009
    )
    assert first == repeated
    assert len(first) == len(NULL_POLICY_CONDITIONS) * 3
    assert not any(item.exceeds_null for item in first)
    with pytest.raises(ValueError, match="confirmatory opening"):
        calibrate_null_policy_accuracy(dataset, "sealed", permutations=1)


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


def _same_rule_rate_among_actionable(dataset: BenchmarkDataset, partition_name: str) -> float:
    """Share of actionable visible evidence that belongs to the task's own latent rule.

    "Actionable" means the record's ``action`` appears in the task's ``allowed_actions``.
    Under an opaque shared namespace this selects nothing about the rule, so the rate sits
    at the base rate ``1 / rule_count``. Under a rule-specific namespace it goes to 1.0,
    which is what the action-namespace leak was.
    """
    partition = next(item for item in dataset.partitions if item.name == partition_name)
    rule_count = len({item.rule_id for item in partition.records})
    actionable = 0
    same_rule = 0
    for task in partition.tasks:
        allowed = set(task.allowed_actions)
        for record in partition.records:
            if record.sequence >= task.sequence or record.deleted:
                continue
            if record.workspace_id != task.workspace_id:
                continue
            if record.action not in allowed:
                continue
            actionable += 1
            if record.rule_id == task.rule_id:
                same_rule += 1
    assert actionable > 0, "no actionable evidence; the namespace check would be vacuous"
    return same_rule / actionable


def test_action_namespace_carries_no_rule_information() -> None:
    """Bind the opaque action namespace to the recorded oracle ceiling.

    The ceiling that the instrument-acceptance bands are frozen against is produced by an
    answer stage aggregating ``observed_action`` weighted by ``observed_outcome``. That is
    the same field pair that carried the action-namespace leak, where ``allowed_actions``
    fingerprinted the latent rule exactly and ``observed_action`` completed the join.

    The ceiling is therefore valid *only while the namespace carries no rule-correlated
    semantics*. If this test fails, the recorded ceiling and every band derived from it are
    invalid and must be recomputed before any confirmatory run. See
    ``research/research-contract-v0.8.json`` -> ``invariants.ceiling_namespace_binding``.
    """
    dataset = generate_dataset(1729, 481516)
    for partition in dataset.partitions:
        signatures = {tuple(sorted(task.allowed_actions)) for task in partition.tasks}
        assert len(signatures) == 1, (
            f"{partition.name}: allowed_actions must not distinguish rules; "
            f"found {len(signatures)} distinct signatures"
        )
        rule_count = len({item.rule_id for item in partition.records})
        base_rate = 1.0 / rule_count
        rate = _same_rule_rate_among_actionable(dataset, partition.name)
        assert rate == pytest.approx(base_rate, abs=0.02), (
            f"{partition.name}: actionable evidence is {rate:.4f} same-rule against a "
            f"base rate of {base_rate:.4f}; the action namespace has regained "
            "rule-correlated semantics and the recorded ceiling is invalid"
        )
