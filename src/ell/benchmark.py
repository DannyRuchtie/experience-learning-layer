"""Deterministic Phase 1 benchmark generator and baseline runner."""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field

from ell.contracts import (
    ApplicationReceipt,
    CostTrace,
    EvaluatorJudgment,
    RunManifest,
)
from ell.identifiers import canonical_json, sha256_digest, stable_id

BENCHMARK_VERSION = "ell-benchmark.v0.1"


class BenchmarkModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExperienceRecord(BenchmarkModel):
    record_id: str
    workspace_id: str
    sequence: int = Field(ge=0)
    observed_time: datetime
    text: str
    scope: str
    action: str
    outcome: float
    outcome_observed_time: datetime
    relation: str = Field(pattern=r"^(supports|contradicts|exception|distractor)$")
    permission: str = Field(default="benchmark", pattern=r"^(benchmark|denied)$")
    deleted: bool = False
    regime: int = Field(default=0, ge=0)
    change_point: bool = False
    correlation_group: Optional[str] = None


class TaskCase(BenchmarkModel):
    task_id: str
    workspace_id: str
    sequence: int = Field(ge=0)
    observed_time: datetime
    query: str
    scope: str
    allowed_actions: List[str]
    gold_action: str
    gold_evidence_ids: List[str]
    gold_counterevidence_ids: List[str]


class BenchmarkPartition(BenchmarkModel):
    name: str = Field(pattern=r"^(train|development|sealed)$")
    records: List[ExperienceRecord]
    tasks: List[TaskCase]


class BenchmarkDataset(BenchmarkModel):
    benchmark_version: str = BENCHMARK_VERSION
    generator_id: str
    seed_commitment: str
    partitions: List[BenchmarkPartition]

    @property
    def dataset_hash(self) -> str:
        return sha256_digest(self)


class BaselineTaskResult(BenchmarkModel):
    task_id: str
    prediction: str
    selected_record_ids: List[str]
    scores: List[float]
    correct: bool
    cost: CostTrace


class BaselineRun(BenchmarkModel):
    baseline_id: str
    partition: str
    dataset_hash: str
    task_results: List[BaselineTaskResult]
    accuracy: float
    evidence_precision: float
    receipts: List[ApplicationReceipt]
    judgments: List[EvaluatorJudgment]
    manifest: RunManifest

    @property
    def result_hash(self) -> str:
        return sha256_digest(self)


RULES: Tuple[Tuple[str, str, str, Tuple[str, ...], Tuple[str, ...]], ...] = (
    (
        "cross-functional-launch",
        "start_review_early",
        "wait_until_locked",
        (
            "External dependencies improved when stakeholder input began before commitment.",
            "A multi-team delivery succeeded after reviewers joined during planning.",
            "Late stakeholder involvement preceded another delayed launch.",
        ),
        (
            "An independently executable task finished without early stakeholder review.",
            "A cosmetic-only change did not need cross-team review.",
        ),
    ),
    (
        "sensitive-export",
        "keep_local",
        "send_remote",
        (
            "Restricted material stayed controlled when processing remained on the device.",
            "A confidential workspace avoided egress by choosing the local path.",
            "Remote processing caused a policy failure for protected records.",
        ),
        (
            "Public demo data was permitted to use a remote service.",
            "An explicitly consented open corpus could leave the device.",
        ),
    ),
    (
        "owner-handoff",
        "confirm_owner",
        "assume_owner",
        (
            "Delivery recovered after a named owner accepted the handoff.",
            "Explicit ownership confirmation prevented a task from being dropped.",
            "An assumed handoff failed because nobody accepted responsibility.",
        ),
        (
            "A solo task had no ownership boundary to confirm.",
            "An automated atomic job completed without a human handoff.",
        ),
    ),
)

TASK_QUERIES = {
    "cross-functional-launch": (
        "How should we prepare an interdependent programme before the plan becomes fixed?",
        "A new initiative crosses organisational boundaries; what is the safer next step?",
    ),
    "sensitive-export": (
        "Choose the processing route for protected material with no egress consent.",
        "What execution location respects this private-data constraint?",
    ),
    "owner-handoff": (
        "A responsibility is moving between people. What must happen next?",
        "How do we stop this transferred obligation from falling between roles?",
    ),
}


def generate_dataset(seed: int, sealed_seed: int) -> BenchmarkDataset:
    """Generate chronological streams; the sealed seed is committed, not serialized."""
    partitions = [
        _generate_partition("train", seed, 0, 50, 30),
        _generate_partition("development", seed + 1, 100, 200, 120),
        _generate_partition("sealed", sealed_seed, 200, 1_000, 640),
    ]
    return BenchmarkDataset(
        generator_id="ell.deterministic-latent-stream.v1",
        seed_commitment=sha256_digest({"sealed_seed": sealed_seed}),
        partitions=partitions,
    )


def generate_development_dataset(seed: int, sealed_seed_commitment: str) -> BenchmarkDataset:
    """Generate only open partitions so development cannot inspect sealed cases."""
    return BenchmarkDataset(
        generator_id="ell.deterministic-latent-stream.v1",
        seed_commitment=sealed_seed_commitment,
        partitions=[
            _generate_partition("train", seed, 0, 50, 30),
            _generate_partition("development", seed + 1, 100, 200, 120),
        ],
    )


def _generate_partition(
    name: str, seed: int, sequence_offset: int, target_records: int, target_tasks: int
) -> BenchmarkPartition:
    rng = random.Random(seed)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=sequence_offset)
    records: List[ExperienceRecord] = []
    tasks: List[TaskCase] = []
    sequence = sequence_offset
    per_rule = [target_records // len(RULES)] * len(RULES)
    for index in range(target_records % len(RULES)):
        per_rule[index] += 1
    tasks_per_rule = [target_tasks // len(RULES)] * len(RULES)
    for index in range(target_tasks % len(RULES)):
        tasks_per_rule[index] += 1
    for rule_index, (rule_id, preferred, rejected, support_phrases, exceptions) in enumerate(RULES):
        evidence_ids: List[str] = []
        counter_ids: List[str] = []
        rule_records = per_rule[rule_index] - 1
        change_index = max(3, int(rule_records * 0.75))
        active_action = preferred
        for index in range(rule_records):
            at_change = index == change_index
            if at_change:
                active_action = rejected
                counter_ids.extend(evidence_ids)
                evidence_ids = []
            is_exception = index % 11 == 10
            is_contradiction = not is_exception and index % 7 == 6
            alternative = preferred if active_action == rejected else rejected
            if is_exception:
                text = exceptions[index % len(exceptions)]
                action = alternative
                relation = "exception"
                outcome = 1.0
            elif is_contradiction:
                text = support_phrases[index % len(support_phrases)]
                action = alternative
                relation = "contradicts"
                outcome = 0.0
            else:
                text = support_phrases[index % len(support_phrases)]
                action = active_action
                relation = "supports"
                outcome = 1.0
            if index >= change_index:
                text += " The governing condition has changed for later decisions."
            text = _paraphrase(text, rng)
            record_id = stable_id("record", name, rule_id, sequence, text)
            permission = "denied" if index == max(1, rule_records // 3) else "benchmark"
            deleted = index == max(2, rule_records // 2)
            observed_time = base + timedelta(hours=sequence - sequence_offset)
            record = ExperienceRecord(
                record_id=record_id,
                workspace_id="workspace-alpha",
                sequence=sequence,
                observed_time=observed_time,
                text=text,
                scope=rule_id if not is_exception else f"{rule_id}:exception",
                action=action,
                outcome=outcome,
                outcome_observed_time=observed_time + timedelta(days=(index % 5) + 1),
                relation=relation,
                permission=permission,
                deleted=deleted,
                regime=1 if index >= change_index else 0,
                change_point=at_change,
                correlation_group=f"{rule_id}:{index // 3}",
            )
            records.append(record)
            if permission == "benchmark" and not deleted:
                (counter_ids if is_exception or outcome == 0.0 else evidence_ids).append(record_id)
            sequence += 1
        distractor = ExperienceRecord(
            record_id=stable_id("record", name, rule_id, "distractor"),
            workspace_id="workspace-alpha",
            sequence=sequence,
            observed_time=base + timedelta(hours=sequence - sequence_offset),
            text="The team selected a blue cover for the internal report.",
            scope="visual-style",
            action="choose_blue",
            outcome=1.0,
            outcome_observed_time=base + timedelta(hours=sequence - sequence_offset, days=1),
            relation="distractor",
        )
        records.append(distractor)
        sequence += 1
        for task_index in range(tasks_per_rule[rule_index]):
            query = TASK_QUERIES[rule_id][task_index % len(TASK_QUERIES[rule_id])]
            query = f"Scenario {task_index + 1}. {query}"
            task_id = stable_id("task", name, rule_id, task_index)
            tasks.append(
                TaskCase(
                    task_id=task_id,
                    workspace_id="workspace-alpha",
                    sequence=sequence,
                    observed_time=base + timedelta(hours=sequence - sequence_offset),
                    query=query,
                    scope=rule_id,
                    allowed_actions=[preferred, rejected, "abstain"],
                    gold_action=active_action,
                    gold_evidence_ids=evidence_ids,
                    gold_counterevidence_ids=counter_ids,
                )
            )
            sequence += 1
    return BenchmarkPartition(name=name, records=records, tasks=tasks)


def _paraphrase(text: str, rng: random.Random) -> str:
    substitutions = {
        "improved": ("worked better", "became more reliable"),
        "succeeded": ("went well", "met its goal"),
        "prevented": ("avoided", "stopped"),
        "failed": ("did not succeed", "broke down"),
        "local": ("on-device", "device-resident"),
    }
    result = text
    for word, alternatives in substitutions.items():
        if word in result:
            result = result.replace(word, rng.choice(alternatives))
    return result


def run_baseline(dataset: BenchmarkDataset, partition_name: str, baseline_id: str) -> BaselineRun:
    """Run one frozen deterministic baseline and emit receipts and judgments."""
    partition = next(item for item in dataset.partitions if item.name == partition_name)
    selector = BASELINES[baseline_id]
    task_results: List[BaselineTaskResult] = []
    receipts: List[ApplicationReceipt] = []
    judgments: List[EvaluatorJudgment] = []
    run_id = stable_id("run", dataset.dataset_hash, partition_name, baseline_id)
    total_cost = CostTrace()
    for task in partition.tasks:
        selected, scores = selector(task, partition.records)
        prediction = _predict(selected)
        correct = prediction == task.gold_action
        selected_ids = [item.record_id for item in selected]
        input_tokens = sum(len(_tokens(item.text)) for item in selected) + len(_tokens(task.query))
        cost = CostTrace(input_tokens=input_tokens, output_tokens=1)
        total_cost = _add_cost(total_cost, cost)
        task_results.append(
            BaselineTaskResult(
                task_id=task.task_id,
                prediction=prediction,
                selected_record_ids=selected_ids,
                scores=scores,
                correct=correct,
                cost=cost,
            )
        )
        receipt = ApplicationReceipt(
            application_id=stable_id("application", run_id, task.task_id),
            run_id=run_id,
            workspace_id=task.workspace_id,
            task_id=task.task_id,
            selected_record_ids=selected_ids,
            concept_versions=[],
            restored_evidence=[],
            decision=prediction,
            policy_id=baseline_id,
            model_id="deterministic",
            cost=cost,
            observed_time=task.observed_time,
        )
        receipts.append(receipt)
        selected_gold = set(selected_ids) & set(task.gold_evidence_ids)
        judgments.append(
            EvaluatorJudgment(
                judgment_id=stable_id("judgment", run_id, task.task_id),
                run_id=run_id,
                task_id=task.task_id,
                evaluator_id="gold-deterministic-v1",
                system_blinded=True,
                success=correct,
                unsupported_generalization=any(
                    item.scope.endswith(":exception") for item in selected
                ),
                cited_support_ids=sorted(selected_gold),
                missed_counterevidence_ids=sorted(
                    set(task.gold_counterevidence_ids) - set(selected_ids)
                ),
            )
        )
    accuracy = sum(item.correct for item in task_results) / max(len(task_results), 1)
    precision_values = []
    for task, result in zip(partition.tasks, task_results):
        predicted = set(result.selected_record_ids)
        precision_values.append(
            len(predicted & set(task.gold_evidence_ids)) / max(len(predicted), 1)
        )
    configuration = {
        "baseline": baseline_id,
        "partition": partition_name,
        "benchmark": dataset.benchmark_version,
        "retrieval_budget": 5,
    }
    manifest = RunManifest(
        run_id=run_id,
        benchmark_version=dataset.benchmark_version,
        partition=partition_name,
        dataset_hash=dataset.dataset_hash,
        configuration_hash=sha256_digest(configuration),
        generator_id=dataset.generator_id,
        seed_commitment=dataset.seed_commitment,
        policy_id=baseline_id,
        model_id="deterministic",
        logical_started_at=partition.records[0].observed_time,
        cost=total_cost,
        environment={
            "python": platform.python_version(),
            "platform": platform.system().lower(),
        },
    )
    return BaselineRun(
        baseline_id=baseline_id,
        partition=partition_name,
        dataset_hash=dataset.dataset_hash,
        task_results=task_results,
        accuracy=accuracy,
        evidence_precision=sum(precision_values) / max(len(precision_values), 1),
        receipts=receipts,
        judgments=judgments,
        manifest=manifest,
    )


def _predict(records: Sequence[ExperienceRecord]) -> str:
    weighted: Counter[str] = Counter()
    for record in records:
        if record.relation == "exception":
            continue
        weighted[record.action] += 2 if record.outcome > 0 else -1
    return weighted.most_common(1)[0][0] if weighted else "abstain"


def _no_memory(
    task: TaskCase, records: Sequence[ExperienceRecord]
) -> Tuple[List[ExperienceRecord], List[float]]:
    return [], []


def _maximum_context(
    task: TaskCase, records: Sequence[ExperienceRecord]
) -> Tuple[List[ExperienceRecord], List[float]]:
    selected = [item for item in records if not item.deleted and item.permission == "benchmark"]
    return selected, [1.0] * len(selected)


def _bm25(
    task: TaskCase, records: Sequence[ExperienceRecord]
) -> Tuple[List[ExperienceRecord], List[float]]:
    documents = [_tokens(item.text) for item in records]
    query = _tokens(task.query)
    average_length = sum(map(len, documents)) / max(len(documents), 1)
    document_frequency = Counter(token for document in documents for token in set(document))
    ranked = []
    for record, document in zip(records, documents):
        frequencies = Counter(document)
        score = 0.0
        for token in query:
            count = frequencies[token]
            if not count:
                continue
            inverse = math.log(
                1
                + (len(documents) - document_frequency[token] + 0.5)
                / (document_frequency[token] + 0.5)
            )
            score += (
                inverse
                * (count * 2.5)
                / (count + 1.5 * (1 - 0.75 + 0.75 * len(document) / max(average_length, 1)))
            )
        ranked.append((score, record))
    return _top(ranked)


def _exact_vector(
    task: TaskCase, records: Sequence[ExperienceRecord]
) -> Tuple[List[ExperienceRecord], List[float]]:
    query_vector = _trigram_vector(task.query)
    ranked = [(_cosine(query_vector, _trigram_vector(item.text)), item) for item in records]
    return _top(ranked)


def _fused(
    task: TaskCase, records: Sequence[ExperienceRecord]
) -> Tuple[List[ExperienceRecord], List[float]]:
    bm_records, _ = _bm25(task, records)
    vector_records, _ = _exact_vector(task, records)
    ranks: Dict[str, float] = {}
    by_id = {item.record_id: item for item in records}
    for selected in (bm_records, vector_records):
        for rank, item in enumerate(selected):
            ranks[item.record_id] = ranks.get(item.record_id, 0.0) + 1.0 / (60 + rank)
    ranked = [(score, by_id[record_id]) for record_id, score in ranks.items()]
    return _top(ranked)


def _rolling_summary(
    task: TaskCase, records: Sequence[ExperienceRecord]
) -> Tuple[List[ExperienceRecord], List[float]]:
    relevant = [
        item
        for item in records
        if item.scope == task.scope and not item.deleted and item.permission == "benchmark"
    ]
    selected = relevant[-5:]
    return selected, [float(item.sequence) for item in selected]


def _direct_insight(
    task: TaskCase, records: Sequence[ExperienceRecord]
) -> Tuple[List[ExperienceRecord], List[float]]:
    relevant = [
        item
        for item in records
        if item.scope == task.scope
        and item.relation in {"supports", "contradicts"}
        and not item.deleted
        and item.permission == "benchmark"
    ]
    selected = sorted(relevant, key=lambda item: (-item.outcome, -item.sequence))[:5]
    return selected, [item.outcome for item in selected]


def _top(
    ranked: Iterable[Tuple[float, ExperienceRecord]],
) -> Tuple[List[ExperienceRecord], List[float]]:
    eligible = [
        (score, record)
        for score, record in ranked
        if score > 0 and not record.deleted and record.permission == "benchmark"
    ]
    eligible.sort(key=lambda item: (-item[0], item[1].record_id))
    chosen = eligible[:5]
    return [record for _, record in chosen], [score for score, _ in chosen]


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _trigram_vector(text: str) -> Dict[str, float]:
    normalized = " ".join(_tokens(text))
    return dict(Counter(normalized[index : index + 3] for index in range(len(normalized) - 2)))


def _cosine(left: Dict[str, float], right: Dict[str, float]) -> float:
    numerator = sum(value * right.get(key, 0.0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _add_cost(left: CostTrace, right: CostTrace) -> CostTrace:
    return CostTrace(
        input_tokens=left.input_tokens + right.input_tokens,
        output_tokens=left.output_tokens + right.output_tokens,
        embedding_tokens=left.embedding_tokens + right.embedding_tokens,
        model_calls=left.model_calls + right.model_calls,
        latency_ms=left.latency_ms + right.latency_ms,
        hardware_seconds=left.hardware_seconds + right.hardware_seconds,
        storage_bytes=left.storage_bytes + right.storage_bytes,
    )


BASELINES: Dict[
    str,
    Callable[[TaskCase, Sequence[ExperienceRecord]], Tuple[List[ExperienceRecord], List[float]]],
] = {
    "no-memory": _no_memory,
    "maximum-context": _maximum_context,
    "bm25": _bm25,
    "exact-vector": _exact_vector,
    "fused-retrieval": _fused,
    "rolling-summary": _rolling_summary,
    "direct-insight": _direct_insight,
}


def write_artifacts(output: Path, dataset: BenchmarkDataset, partition: str) -> None:
    """Write canonical dataset and all deterministic baseline traces."""
    output.mkdir(parents=True, exist_ok=True)
    if partition != "sealed" and any(item.name == "sealed" for item in dataset.partitions):
        dataset = dataset.model_copy(
            update={"partitions": [item for item in dataset.partitions if item.name != "sealed"]}
        )
    (output / "dataset.json").write_text(canonical_json(dataset) + "\n", encoding="utf-8")
    for baseline_id in BASELINES:
        run = run_baseline(dataset, partition, baseline_id)
        (output / f"{baseline_id}.json").write_text(canonical_json(run) + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--sealed-seed", type=int)
    parser.add_argument("--sealed-commitment")
    parser.add_argument(
        "--partition", choices=("train", "development", "sealed"), default="development"
    )
    parser.add_argument("--output", type=Path, default=Path("artifacts/benchmark"))
    args = parser.parse_args(argv)
    if args.partition == "sealed":
        if args.sealed_seed is None:
            parser.error("--sealed-seed is required when opening the sealed partition")
        dataset = generate_dataset(args.seed, args.sealed_seed)
    else:
        commitment = args.sealed_commitment
        if args.sealed_seed is not None:
            commitment = sha256_digest({"sealed_seed": args.sealed_seed})
        if commitment is None:
            parser.error("provide --sealed-commitment or --sealed-seed")
        dataset = generate_development_dataset(args.seed, commitment)
    write_artifacts(args.output, dataset, args.partition)
    print(json.dumps({"dataset_hash": dataset.dataset_hash, "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
