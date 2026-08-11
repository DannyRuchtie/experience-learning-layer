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
    rule_id: str
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
    rule_id: str
    """Latent-rule identity. This is the cluster label for the primary interval."""

    sequence: int = Field(ge=0)
    observed_time: datetime
    query: str
    scope: str
    transfer: str = Field(pattern=r"^(near|intermediate|far)$")
    """Lexical distance stratum. The primary transfer gate reads only ``far`` tasks."""
    allowed_actions: List[str]
    gold_action: str
    gold_evidence_ids: List[str]
    gold_counterevidence_ids: List[str]
    regime: int = Field(default=0, ge=0)
    """Which governing regime was active when the task was posed."""
    episodes_since_change: Optional[int] = None
    """Contradictory episodes observed since the change point, or None if pre-change.

    The change-adaptation gate is measured against this field: it is what makes
    "revised within two relevant contradictory episodes" a computable quantity.
    """


class PolicyTask(BenchmarkModel):
    """Task projection visible to an eligible policy.

    Generator labels, evaluation strata, and gold answers remain on ``TaskCase``
    and never cross this boundary.
    """

    task_id: str
    workspace_id: str
    sequence: int = Field(ge=0)
    observed_time: datetime
    query: str
    allowed_actions: List[str]


class PolicyRecord(BenchmarkModel):
    """Chronology- and permission-filtered experience visible to a policy."""

    record_id: str
    workspace_id: str
    sequence: int = Field(ge=0)
    observed_time: datetime
    text: str
    observed_action: str
    observed_outcome: Optional[float] = None


class PolicySelection(BenchmarkModel):
    """A policy's scored reference to a runner-issued record."""

    record_id: str
    score: float = Field(ge=0.0)


class BenchmarkPartition(BenchmarkModel):
    name: str = Field(pattern=r"^(train|development|sealed)$")
    records: List[ExperienceRecord]
    tasks: List[TaskCase]


class PositionalLeakAssertion(BenchmarkModel):
    """Generator-time structural assertion that does not inspect task outcomes."""

    partition: str = Field(pattern=r"^(train|development|sealed)$")
    rule_count: int = Field(gt=0)
    same_rule_recent_records: int = Field(ge=0)
    issued_recent_records: int = Field(gt=0)
    observed_rate: float = Field(ge=0.0, le=1.0)
    chance_rate: float = Field(gt=0.0, le=1.0)
    passed: bool


class BenchmarkDataset(BenchmarkModel):
    benchmark_version: str = BENCHMARK_VERSION
    generator_id: str
    seed_commitment: str
    partitions: List[BenchmarkPartition]
    positional_leak_assertions: List[PositionalLeakAssertion]

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


class NullPolicyCalibration(BenchmarkModel):
    """Per-policy A9b accuracy bound from fixed outputs and permuted gold trajectories."""

    policy_id: str
    partition: str = Field(pattern=r"^(train|development)$")
    stratum: str = Field(pattern=r"^(near|intermediate|far)$")
    permutations: int = Field(gt=0)
    permutation_seed: int
    fixed_output_hash: str
    observed_accuracy: float = Field(ge=0.0, le=1.0)
    null_p95: float = Field(ge=0.0, le=1.0)
    exceeds_null: bool


# ---------------------------------------------------------------------------
# Latent rule construction
# ---------------------------------------------------------------------------
#
# The unit of generalisation in this benchmark is the *latent rule*, not the task
# instance. Tasks generated from one rule share a gold action, an evidence set,
# and a surface template, so they are not independent observations. The primary
# interval is therefore a cluster bootstrap over rule identity (see
# ell.statistics.paired_cluster_bootstrap_interval), and the number of distinct
# rules governs the effective sample size of the design.
#
# Because of that, rule count is a declared design parameter rather than a
# hand-written list. Rules are composed deterministically from orthogonal domain
# vocabularies so that each rule has its own scope, action pair, evidence
# phrasing, and query phrasing. Query wording deliberately shares little surface
# vocabulary with the supporting evidence: structurally related, lexically
# distant retrieval is the behaviour under test.

MINIMUM_SEALED_RULES = 32
"""Phase 1 exit requirement.

Below roughly this many rules the cluster bootstrap is untrustworthy and the
task-level interval overstates precision by a factor large enough to reverse a
verdict. Measured design effects: 1.67x at 3 rules, 1.62x at 12, 1.11x at 32.
"""


class LatentRule(BenchmarkModel):
    rule_id: str
    scope: str
    preferred_action: str
    rejected_action: str
    support_phrases: List[str]
    exception_phrases: List[str]
    near_query_templates: List[str]
    """Queries that reuse the evidence vocabulary. Lexical retrieval can serve these."""
    intermediate_query_templates: List[str]
    """Queries retaining the domain vocabulary but paraphrasing the mechanism."""
    far_query_templates: List[str]
    """Queries with zero content-word overlap with the evidence. The transfer test."""


# Each domain supplies two disjoint noun vocabularies: one used only when writing
# evidence, one used only when writing queries. Nothing lexical bridges them. A
# system can only connect a query to its supporting episodes through the latent
# structure, which is precisely the capability the primary transfer gate tests.
#
# (domain token, evidence subject, query subject)
_DOMAINS: Tuple[Tuple[str, str, str], ...] = (
    (
        "launch",
        "interdependent delivery",
        "programme spanning several groups",
    ),
    (
        "export",
        "protected material",
        "records carrying a confidentiality label",
    ),
    (
        "handoff",
        "transferred obligation",
        "duty passing from one person to another",
    ),
    (
        "estimate",
        "sizing commitment",
        "figure quoted to a customer",
    ),
    (
        "vendor",
        "third-party engagement",
        "agreement with an outside supplier",
    ),
    (
        "migration",
        "schema change",
        "alteration to a live data structure",
    ),
    (
        "hiring",
        "panel decision",
        "group verdict on a candidate",
    ),
    (
        "incident",
        "degraded service",
        "customer-visible malfunction",
    ),
    (
        "pricing",
        "contract exception",
        "discount outside the published rate",
    ),
)

# Mechanism templates are likewise split. The evidence template names the
# mechanism directly; the query template gestures at it without reusing the word.
#
# (mechanism, evidence template, exception template, near question, far question)
_MECHANISMS: Tuple[Tuple[str, str, str, str, str], ...] = (
    (
        "sequence",
        "{subject} held together because the ordering constraint was respected before commitment",
        "an isolated {subject} carried no ordering constraint at all",
        "What ordering constraint should {subject} respect before commitment?",
        "Which steps of {subject} have to happen while the plan can still move?",
    ),
    (
        "authority",
        "{subject} was resolved once a named decision-maker accepted responsibility",
        "a fully delegated {subject} had its authority settled already",
        "Which named decision-maker must accept responsibility for {subject}?",
        "Whose sign-off does {subject} depend on to avoid stalling?",
    ),
    (
        "reversibility",
        "{subject} recovered because the chosen step could still be undone",
        "a trivially repeatable {subject} raised no reversibility concern",
        "Can the step chosen for {subject} still be undone?",
        "How much of {subject} should we be able to walk back later?",
    ),
    (
        "disclosure",
        "{subject} avoided harm when the constraint was stated in writing up front",
        "a {subject} with no external readers needed nothing written down",
        "Which constraint should {subject} state in writing up front?",
        "What must be put on record before {subject} goes ahead?",
    ),
    (
        "verification",
        "{subject} succeeded because an independent check ran before the result was trusted",
        "a self-evidently checkable {subject} required no independent check",
        "Which independent check should {subject} run before the result is trusted?",
        "Who else needs to look at {subject} before we rely on the answer?",
    ),
    (
        "budget",
        "{subject} stayed viable because the spending ceiling was agreed in advance",
        "a zero-cost {subject} had no ceiling to agree",
        "Which spending ceiling should {subject} agree in advance?",
        "What limit keeps {subject} from quietly growing past what we can afford?",
    ),
)


def build_latent_rules(count: int, action_seed: int) -> Tuple[LatentRule, ...]:
    """Compose ``count`` deterministic latent rules from orthogonal vocabularies."""
    if count < 1:
        raise ValueError("count must be positive")
    available = len(_DOMAINS) * len(_MECHANISMS)
    if count > available:
        raise ValueError(f"cannot compose {count} distinct rules from {available} combinations")
    preferred_labels = ["option_a"] * (count // 2) + ["option_b"] * (count - count // 2)
    action_rng = random.Random(action_seed ^ 0xAC710)
    action_rng.shuffle(preferred_labels)
    rules: List[LatentRule] = []
    for index in range(count):
        domain_token, evidence_subject, query_subject = _DOMAINS[
            index % len(_DOMAINS)
        ]
        mechanism, support, exception, near_question, far_question = _MECHANISMS[
            index // len(_DOMAINS)
        ]
        rule_id = f"{domain_token}-{mechanism}"
        preferred = preferred_labels[index]
        rejected = "option_b" if preferred == "option_a" else "option_a"
        rules.append(
            LatentRule(
                rule_id=rule_id,
                scope=rule_id,
                preferred_action=preferred,
                rejected_action=rejected,
                support_phrases=[
                    support.format(subject=f"A {evidence_subject}").rstrip(".") + ".",
                    support.format(subject=f"A second {evidence_subject}").rstrip(".") + ".",
                    f"An equivalent {evidence_subject} broke down when that "
                    "condition was skipped.",
                ],
                exception_phrases=[
                    exception.format(subject=f"By contrast, {evidence_subject}").rstrip(".") + ".",
                    f"A purely cosmetic {evidence_subject} carried none of that risk.",
                ],
                near_query_templates=[
                    near_question.format(subject=f"a further {evidence_subject}"),
                    near_question.format(subject=f"another {evidence_subject}"),
                ],
                intermediate_query_templates=[
                    far_question.format(subject=f"a further {evidence_subject}"),
                    far_question.format(subject=f"another {evidence_subject}"),
                ],
                far_query_templates=[
                    far_question.format(subject=f"a {query_subject}"),
                    far_question.format(subject=f"this new {query_subject}"),
                    f"Something unfamiliar has come up. "
                    f"{far_question.format(subject=f'a {query_subject}')}",
                    f"Advise on an unplanned case involving a {query_subject}.",
                ],
            )
        )
    return tuple(rules)


# (rules, records, paired tasks) per chronological partition.
#
# Sealed sizing is derived, not chosen. 54 latent rules x 56 paired tasks = 3,024.
#
#   rules      54  >= MINIMUM_SEALED_RULES (32), so the cluster bootstrap is sound
#   far tasks 1512 >= 1,294 required for 0.95 power at a five-point effect and a
#                    0.25 discordant-pair rate. The primary gate reads only the far
#                    stratum, so far-task count is the binding constraint, not N.
#   all tasks 3024 >= 1,625 required for the unsupported-generalisation gate to reach
#                    0.95 power against a two-point margin at 0.05 discordance. That
#                    gate is measured on both strata, since applying a concept outside
#                    its scope is observable regardless of lexical distance.
#
# Rule count was raised in preference to tasks per rule. Adding tasks to an existing
# rule mostly duplicates query templates and buys little precision once tasks are
# clustered; adding rules buys precision and external validity together.
# See research/research-contract-v0.7.json and ell.statistics.
TRAIN_TIER = (12, 420, 240)
DEVELOPMENT_TIER = (24, 840, 1_008)
SEALED_TIER = (54, 1_890, 3_024)


def generate_dataset(seed: int, sealed_seed: int) -> BenchmarkDataset:
    """Generate chronological streams; the sealed seed is committed, not serialized."""
    partitions = [
        _generate_partition("train", seed, 0, *TRAIN_TIER),
        _generate_partition("development", seed + 1, 400, *DEVELOPMENT_TIER),
        _generate_partition("sealed", sealed_seed, 1_600, *SEALED_TIER),
    ]
    return BenchmarkDataset(
        generator_id="ell.deterministic-latent-stream.v1",
        seed_commitment=sha256_digest({"sealed_seed": sealed_seed}),
        partitions=partitions,
        positional_leak_assertions=[
            _positional_leak_assertion(partition) for partition in partitions
        ],
    )


def generate_development_dataset(seed: int, sealed_seed_commitment: str) -> BenchmarkDataset:
    """Generate only open partitions so development cannot inspect sealed cases."""
    partitions = [
        _generate_partition("train", seed, 0, *TRAIN_TIER),
        _generate_partition("development", seed + 1, 400, *DEVELOPMENT_TIER),
    ]
    return BenchmarkDataset(
        generator_id="ell.deterministic-latent-stream.v1",
        seed_commitment=sealed_seed_commitment,
        partitions=partitions,
        positional_leak_assertions=[
            _positional_leak_assertion(partition) for partition in partitions
        ],
    )


def _generate_partition(
    name: str,
    seed: int,
    sequence_offset: int,
    rule_count: int,
    target_records: int,
    target_tasks: int,
) -> BenchmarkPartition:
    rng = random.Random(seed)
    structure_rng = random.Random(seed ^ 0x57A7C7)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=sequence_offset)
    records: List[ExperienceRecord] = []
    tasks: List[TaskCase] = []
    sequence = sequence_offset
    rules = build_latent_rules(rule_count, seed)
    per_rule = [target_records // len(rules)] * len(rules)
    for index in range(target_records % len(rules)):
        per_rule[index] += 1
    tasks_per_rule = [target_tasks // len(rules)] * len(rules)
    for index in range(target_tasks % len(rules)):
        tasks_per_rule[index] += 1

    # Pair opposite action mappings onto the same sampled structural profile. This
    # varies change points and outcome events across rules and seeds while preserving
    # exact record-weighted A/B balance: every profile has a mirrored action twin.
    preferred_a = [
        index for index, rule in enumerate(rules) if rule.preferred_action == "option_a"
    ]
    preferred_b = [
        index for index, rule in enumerate(rules) if rule.preferred_action == "option_b"
    ]
    structure_profiles: Dict[int, Tuple[int, List[bool], List[bool]]] = {}
    for left, right in zip(preferred_a, preferred_b):
        rule_records = per_rule[left] - 1
        change_index = max(3, int(rule_records * structure_rng.uniform(0.5, 0.7)))
        exception_probability = structure_rng.uniform(0.06, 0.12)
        contradiction_probability = structure_rng.uniform(0.10, 0.18)
        exception_pattern = [
            structure_rng.random() < exception_probability
            for _ in range(rule_records)
        ]
        contradiction_pattern = [
            not exception and structure_rng.random() < contradiction_probability
            for exception in exception_pattern
        ]
        profile = (change_index, exception_pattern, contradiction_pattern)
        structure_profiles[left] = profile
        structure_profiles[right] = profile

    # Cluster permutations require trajectories to align by ordinal and stratum.
    # Sample their shared order per partition so position/stratum structure changes
    # across seeds without destroying that alignment.
    max_task_count = max(tasks_per_rule)
    shared_task_strata = [
        ("near", "intermediate", "far")[index % 3]
        for index in range(max_task_count)
    ]
    structure_rng.shuffle(shared_task_strata)
    for rule_index, rule in enumerate(rules):
        rule_id = rule.rule_id
        preferred = rule.preferred_action
        rejected = rule.rejected_action
        support_phrases = rule.support_phrases
        exceptions = rule.exception_phrases
        rule_records = per_rule[rule_index] - 1
        change_index, exception_flags, contradiction_flags = structure_profiles[
            rule_index
        ]

        # Tasks are interleaved into the stream rather than appended after it.
        #
        # Appending every task after the whole rule stream gave all tasks of a rule
        # the same gold action, which made them near-perfectly correlated: the
        # effective sample size collapsed to the rule count regardless of how many
        # tasks were generated, and no policy could be credited for tracking the
        # change point because there was nothing to track by the time it was asked.
        # Interleaving means a task posed before the change point has the earlier
        # gold action and a task posed after it has the later one, so within-rule
        # tasks carry independent information and temporal adaptation is measurable.
        task_count = tasks_per_rule[rule_index]
        # Spread task positions across the rule's stream. Positions may repeat when a
        # rule carries more tasks than stream slots; they must not be forced distinct,
        # because requiring distinct slots cannot terminate in that case.
        first_slot, last_slot = 2, max(2, rule_records - 1)
        span = last_slot - first_slot
        task_positions = [
            first_slot + (round(index * span / max(task_count - 1, 1)) if span else 0)
            for index in range(task_count)
        ]
        task_strata = shared_task_strata[:task_count]
        pending: Dict[int, List[int]] = {}
        for task_index, position in enumerate(task_positions[:task_count]):
            pending.setdefault(position, []).append(task_index)

        evidence_ids: List[str] = []
        counter_ids: List[str] = []
        active_action = preferred
        for index in range(rule_records):
            at_change = index == change_index
            if at_change:
                active_action = rejected
                counter_ids.extend(evidence_ids)
                evidence_ids = []
            is_exception = exception_flags[index]
            is_contradiction = contradiction_flags[index]
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
                rule_id=rule_id,
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

            # Emit any task scheduled at this point in the stream. Gold state is
            # whatever the stream has established so far, never what comes later.
            for task_index in pending.get(index, []):
                stratum = task_strata[task_index]
                templates = {
                    "near": rule.near_query_templates,
                    "intermediate": rule.intermediate_query_templates,
                    "far": rule.far_query_templates,
                }[stratum]
                query = templates[(task_index // 3) % len(templates)]
                query = f"Scenario {task_index + 1}. {query}"
                episodes_since_change = index - change_index if index >= change_index else None
                tasks.append(
                    TaskCase(
                        task_id=stable_id("task", name, rule_id, task_index),
                        workspace_id="workspace-alpha",
                        rule_id=rule_id,
                        sequence=sequence,
                        observed_time=base + timedelta(hours=sequence - sequence_offset),
                        query=query,
                        scope=rule_id,
                        transfer=stratum,
                        allowed_actions=[preferred, rejected, "abstain"],
                        gold_action=active_action,
                        gold_evidence_ids=list(evidence_ids),
                        gold_counterevidence_ids=list(counter_ids),
                        regime=1 if index >= change_index else 0,
                        episodes_since_change=episodes_since_change,
                    )
                )
                sequence += 1

        distractor = ExperienceRecord(
            record_id=stable_id("record", name, rule_id, "distractor"),
            workspace_id="workspace-beta",
            rule_id=rule_id,
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
    records, tasks = _interleave_rule_streams(
        records,
        tasks,
        [rule.rule_id for rule in rules],
        seed,
        sequence_offset,
        base,
    )
    return BenchmarkPartition(name=name, records=records, tasks=tasks)


def _interleave_rule_streams(
    records: Sequence[ExperienceRecord],
    tasks: Sequence[TaskCase],
    rule_ids: Sequence[str],
    seed: int,
    sequence_offset: int,
    base: datetime,
) -> Tuple[List[ExperienceRecord], List[TaskCase]]:
    """Shuffle rule order per round while preserving every within-rule event order."""
    record_by_id = {item.record_id: item for item in records}
    task_by_id = {item.task_id: item for item in tasks}
    streams: Dict[str, List[Tuple[int, str, str]]] = {
        rule_id: [] for rule_id in rule_ids
    }
    for record in records:
        streams[record.rule_id].append((record.sequence, "record", record.record_id))
    for task in tasks:
        streams[task.rule_id].append((task.sequence, "task", task.task_id))
    for stream in streams.values():
        stream.sort(key=lambda item: item[0])

    schedule_rng = random.Random(seed ^ 0xE11A9E)
    positions = dict.fromkeys(rule_ids, 0)
    active = list(rule_ids)
    ordered: List[Tuple[str, str]] = []
    while active:
        schedule_rng.shuffle(active)
        remaining: List[str] = []
        for rule_id in active:
            position = positions[rule_id]
            _, kind, identifier = streams[rule_id][position]
            ordered.append((kind, identifier))
            positions[rule_id] += 1
            if positions[rule_id] < len(streams[rule_id]):
                remaining.append(rule_id)
        active = remaining

    interleaved_records: List[ExperienceRecord] = []
    interleaved_tasks: List[TaskCase] = []
    for offset, (kind, identifier) in enumerate(ordered):
        sequence = sequence_offset + offset
        observed_time = base + timedelta(hours=offset)
        if kind == "record":
            record = record_by_id[identifier]
            outcome_delay = record.outcome_observed_time - record.observed_time
            interleaved_records.append(
                record.model_copy(
                    update={
                        "sequence": sequence,
                        "observed_time": observed_time,
                        "outcome_observed_time": observed_time + outcome_delay,
                    }
                )
            )
        elif kind == "task":
            task = task_by_id[identifier]
            interleaved_tasks.append(
                task.model_copy(
                    update={"sequence": sequence, "observed_time": observed_time}
                )
            )
        else:
            raise ValueError(f"unknown stream event kind: {kind}")
    return interleaved_records, interleaved_tasks


def _positional_leak_assertion(
    partition: BenchmarkPartition,
) -> PositionalLeakAssertion:
    """Measure rule identity in the recent visible tail without reading task gold."""
    source_by_id = {item.record_id: item for item in partition.records}
    matches = 0
    issued = 0
    for task in partition.tasks:
        visible = project_policy_records(task, partition.records)
        recent = sorted(visible, key=lambda item: item.sequence, reverse=True)[:5]
        matches += sum(
            source_by_id[item.record_id].rule_id == task.rule_id for item in recent
        )
        issued += len(recent)
    rule_count = len({task.rule_id for task in partition.tasks})
    chance = 1 / rule_count
    observed = matches / issued
    standard_error = math.sqrt(chance * (1 - chance) / issued)
    return PositionalLeakAssertion(
        partition=partition.name,
        rule_count=rule_count,
        same_rule_recent_records=matches,
        issued_recent_records=issued,
        observed_rate=observed,
        chance_rate=chance,
        passed=observed <= chance + 3 * standard_error,
    )


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
    source_records = {item.record_id: item for item in partition.records}
    for task in partition.tasks:
        policy_task = project_policy_task(task)
        policy_records = project_policy_records(task, partition.records)
        records_by_id = {item.record_id: item for item in policy_records}
        if baseline_id in ORACLE_CONDITIONS:
            selections = _oracle_select(task, policy_records, baseline_id)
        else:
            assert selector is not None
            selections = selector(policy_task, policy_records)
        _validate_selections(selections, records_by_id)
        prediction = (
            task.gold_action
            if baseline_id == "oracle-concept"
            else _predict(selections, records_by_id)
        )
        correct = prediction == task.gold_action
        selected_ids = [item.record_id for item in selections]
        selected = [records_by_id[item_id] for item_id in selected_ids]
        evaluator_selected = [source_records[item_id] for item_id in selected_ids]
        input_tokens = sum(len(_tokens(item.text)) for item in selected) + len(_tokens(task.query))
        cost = CostTrace(input_tokens=input_tokens, output_tokens=1)
        total_cost = _add_cost(total_cost, cost)
        task_results.append(
            BaselineTaskResult(
                task_id=task.task_id,
                prediction=prediction,
                selected_record_ids=selected_ids,
                scores=[item.score for item in selections],
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
                    item.scope.endswith(":exception") for item in evaluator_selected
                ),
                cited_support_ids=sorted(selected_gold),
                material_counterevidence_ids=sorted(task.gold_counterevidence_ids),
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


def project_policy_task(task: TaskCase) -> PolicyTask:
    """Remove evaluator-only fields before invoking an eligible policy."""
    return PolicyTask(
        task_id=task.task_id,
        workspace_id=task.workspace_id,
        sequence=task.sequence,
        observed_time=task.observed_time,
        query=task.query,
        allowed_actions=task.allowed_actions,
    )


def project_policy_records(
    task: TaskCase, records: Sequence[ExperienceRecord]
) -> List[PolicyRecord]:
    """Issue only records available and authorized at the task's decision time."""
    visible: List[PolicyRecord] = []
    for record in records:
        if record.workspace_id != task.workspace_id:
            continue
        if record.sequence >= task.sequence or record.observed_time > task.observed_time:
            continue
        if record.permission != "benchmark" or record.deleted:
            continue
        visible.append(
            PolicyRecord(
                record_id=record.record_id,
                workspace_id=record.workspace_id,
                sequence=record.sequence,
                observed_time=record.observed_time,
                text=record.text,
                observed_action=record.action,
                observed_outcome=(
                    record.outcome
                    if record.outcome_observed_time <= task.observed_time
                    else None
                ),
            )
        )
    return visible


def _validate_selections(
    selections: Sequence[PolicySelection], records_by_id: Dict[str, PolicyRecord]
) -> None:
    identifiers = [item.record_id for item in selections]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("policy returned duplicate record identifiers")
    unavailable = sorted(set(identifiers) - set(records_by_id))
    if unavailable:
        raise ValueError(f"policy selected records outside runner context: {unavailable}")


def _predict(
    selections: Sequence[PolicySelection], records_by_id: Dict[str, PolicyRecord]
) -> str:
    """Apply a frozen score-aware decision rule to observed outcomes only."""
    weighted: Dict[str, float] = {}
    for rank, selection in enumerate(selections):
        record = records_by_id[selection.record_id]
        if record.observed_outcome is None:
            continue
        retrieval_weight = selection.score / (rank + 1)
        outcome_direction = 1.0 if record.observed_outcome > 0 else -1.0
        weighted[record.observed_action] = (
            weighted.get(record.observed_action, 0.0)
            + retrieval_weight * outcome_direction
        )
    if not weighted:
        return "abstain"
    action, score = sorted(weighted.items(), key=lambda item: (-item[1], item[0]))[0]
    return action if score > 0 else "abstain"


def _no_memory(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    return []


def _maximum_context(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    return [PolicySelection(record_id=item.record_id, score=1.0) for item in records]


def _bm25(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
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
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    query_vector = _trigram_vector(task.query)
    ranked = [(_cosine(query_vector, _trigram_vector(item.text)), item) for item in records]
    return _top(ranked)


def _fused(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    bm_records = _bm25(task, records)
    vector_records = _exact_vector(task, records)
    ranks: Dict[str, float] = {}
    for selected in (bm_records, vector_records):
        for rank, item in enumerate(selected):
            ranks[item.record_id] = ranks.get(item.record_id, 0.0) + 1.0 / (60 + rank)
    ranked = [(score, record_id) for record_id, score in ranks.items()]
    return _top_ids(ranked)


def _rolling_summary(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    """Recency window only.

    Earlier revisions filtered on ``record.scope == task.scope``. That is a gold
    generator label, not something a rolling summary could know, and it handed two
    baselines an oracle shortcut. A rolling summary sees the tail of the stream and
    nothing else.
    """
    selected = sorted(records, key=lambda item: item.sequence, reverse=True)[:5]
    return [
        PolicySelection(record_id=item.record_id, score=1.0)
        for item in selected
    ]


def _uniform_random_visible(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    """Deterministic uniform-like sample carrying no task or record-content signal."""
    selected = sorted(
        records,
        key=lambda item: sha256_digest(
            {"null_policy": "uniform-random", "task": task.task_id, "record": item.record_id}
        ),
    )[:5]
    return [PolicySelection(record_id=item.record_id, score=1.0) for item in selected]


def _record_id_order(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    """Select the five lexicographically lowest opaque identifiers."""
    selected = sorted(records, key=lambda item: item.record_id)[:5]
    return [PolicySelection(record_id=item.record_id, score=1.0) for item in selected]


def _oldest_context(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    """Select the five lowest-sequence visible records."""
    selected = sorted(records, key=lambda item: item.sequence)[:5]
    return [PolicySelection(record_id=item.record_id, score=1.0) for item in selected]


def _action_filter(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    """Select by the allowed/observed-action join and read no text or position."""
    allowed = set(task.allowed_actions) - {"abstain"}
    selected = [item for item in records if item.observed_action in allowed][:5]
    return [PolicySelection(record_id=item.record_id, score=1.0) for item in selected]


def _direct_insight(
    task: PolicyTask, records: Sequence[PolicyRecord]
) -> List[PolicySelection]:
    """Insight extraction over lexically retrieved outcome-bearing episodes.

    Groups by surface similarity to the query rather than by the generator's scope
    label, then prefers episodes whose outcome was observed. This is the strongest
    non-oracle deterministic baseline and the most likely confirmatory comparator.
    """
    query_vector = _trigram_vector(task.query)
    scored = [
        (_cosine(query_vector, _trigram_vector(item.text)), item)
        for item in records
    ]
    eligible = [(score, item) for score, item in scored if score > 0]
    eligible.sort(key=lambda pair: (-pair[0], pair[1].record_id))
    pool = eligible[:12]
    selected = sorted(
        pool,
        key=lambda pair: (
            -(pair[1].observed_outcome if pair[1].observed_outcome is not None else -1.0),
            -pair[0],
            -pair[1].sequence,
        ),
    )[:5]
    return [PolicySelection(record_id=item.record_id, score=score) for score, item in selected]


def _oracle_select(
    task: TaskCase,
    records: Sequence[PolicyRecord],
    baseline_id: str,
) -> List[PolicySelection]:
    """Run an evaluation-only ceiling outside the eligible policy interface."""
    if baseline_id == "oracle-retrieval":
        gold = set(task.gold_evidence_ids) | set(task.gold_counterevidence_ids)
    elif baseline_id == "oracle-concept":
        gold = set(task.gold_evidence_ids)
    else:
        raise ValueError(f"unknown oracle condition: {baseline_id}")
    # The oracle must rank perfect evidence using a policy-visible field. Generator
    # emission order is not a retrieval ranking and materially changes the
    # rank-aware answer stage. Recency is explicit in the issued record sequence.
    selected = sorted(
        (item for item in records if item.record_id in gold),
        key=lambda item: (-item.sequence, item.record_id),
    )
    return [
        PolicySelection(record_id=item.record_id, score=1.0)
        for item in selected
    ]


def _top(
    ranked: Iterable[Tuple[float, PolicyRecord]],
) -> List[PolicySelection]:
    eligible = [(score, record) for score, record in ranked if score > 0]
    eligible.sort(key=lambda item: (-item[0], item[1].record_id))
    chosen = eligible[:5]
    return [PolicySelection(record_id=record.record_id, score=score) for score, record in chosen]


def _top_ids(ranked: Iterable[Tuple[float, str]]) -> List[PolicySelection]:
    eligible = [(score, record_id) for score, record_id in ranked if score > 0]
    eligible.sort(key=lambda item: (-item[0], item[1]))
    return [
        PolicySelection(record_id=record_id, score=score)
        for score, record_id in eligible[:5]
    ]


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


PolicySelector = Callable[[PolicyTask, Sequence[PolicyRecord]], List[PolicySelection]]


BASELINES: Dict[str, Optional[PolicySelector]] = {
    "no-memory": _no_memory,
    "maximum-context": _maximum_context,
    "bm25": _bm25,
    "exact-vector": _exact_vector,
    "fused-retrieval": _fused,
    "rolling-summary": _rolling_summary,
    "uniform-random-visible": _uniform_random_visible,
    "record-id-order": _record_id_order,
    "oldest-context": _oldest_context,
    "action-filter": _action_filter,
    "direct-insight": _direct_insight,
    # Oracle ceilings. Not eligible as the confirmatory comparator: they consume
    # gold generator labels. Reported to bound and interpret the primary result.
    "oracle-retrieval": None,
    "oracle-concept": None,
}

ELIGIBLE_COMPARATORS: Tuple[str, ...] = (
    "bm25",
    "exact-vector",
    "fused-retrieval",
    "rolling-summary",
    "direct-insight",
)
"""Conditions from which the confirmatory comparator may be selected on development data."""

ORACLE_CONDITIONS: Tuple[str, ...] = ("oracle-retrieval", "oracle-concept")
"""Ceiling conditions. Excluded from comparator selection by contract."""

NULL_POLICY_CONDITIONS: Tuple[str, ...] = (
    "uniform-random-visible",
    "rolling-summary",
    "record-id-order",
    "oldest-context",
    "action-filter",
)
"""Signal-free policies used by the A9 leakage battery."""


def calibrate_null_policy_accuracy(
    dataset: BenchmarkDataset,
    partition_name: str,
    *,
    permutations: int = 1_000,
    permutation_seed: int = 90_009,
) -> List[NullPolicyCalibration]:
    """Calibrate A9b per policy while holding every policy output fixed.

    Complete gold-action trajectories are permuted between latent-rule clusters.
    Queries, records, chronology, selections, and predictions never change.
    """
    if partition_name == "sealed":
        raise ValueError("sealed null accuracy is calibrated only after confirmatory opening")
    if permutations < 1:
        raise ValueError("permutations must be positive")
    partition = next(item for item in dataset.partitions if item.name == partition_name)
    tasks_by_rule: Dict[str, List[TaskCase]] = {}
    for task in partition.tasks:
        tasks_by_rule.setdefault(task.rule_id, []).append(task)
    for tasks in tasks_by_rule.values():
        tasks.sort(key=lambda item: item.sequence)
    rule_ids = sorted(tasks_by_rule)
    reference_strata = [item.transfer for item in tasks_by_rule[rule_ids[0]]]
    if any(
        [item.transfer for item in tasks_by_rule[rule_id]] != reference_strata
        for rule_id in rule_ids[1:]
    ):
        raise ValueError("rule trajectories must align by task ordinal and stratum")

    runs = {
        policy_id: run_baseline(dataset, partition_name, policy_id)
        for policy_id in NULL_POLICY_CONDITIONS
    }
    fixed_output_hashes = {
        policy_id: sha256_digest(
            [
                {"task_id": item.task_id, "prediction": item.prediction}
                for item in run.task_results
            ]
        )
        for policy_id, run in runs.items()
    }
    predictions = {
        policy_id: {item.task_id: item.prediction for item in run.task_results}
        for policy_id, run in runs.items()
    }
    task_by_id = {task.task_id: task for task in partition.tasks}
    strata = ("near", "intermediate", "far")
    task_ids_by_stratum = {
        stratum: [task.task_id for task in partition.tasks if task.transfer == stratum]
        for stratum in strata
    }
    null_values: Dict[str, Dict[str, List[float]]] = {
        policy_id: {stratum: [] for stratum in strata}
        for policy_id in NULL_POLICY_CONDITIONS
    }
    permutation_rng = random.Random(permutation_seed)
    for _ in range(permutations):
        donor_rules = list(rule_ids)
        permutation_rng.shuffle(donor_rules)
        permuted_gold: Dict[str, str] = {}
        for target_rule, donor_rule in zip(rule_ids, donor_rules):
            for target_task, donor_task in zip(
                tasks_by_rule[target_rule], tasks_by_rule[donor_rule]
            ):
                permuted_gold[target_task.task_id] = donor_task.gold_action
        for policy_id, policy_predictions in predictions.items():
            for stratum in strata:
                task_ids = task_ids_by_stratum[stratum]
                accuracy = sum(
                    policy_predictions[task_id] == permuted_gold[task_id]
                    for task_id in task_ids
                ) / len(task_ids)
                null_values[policy_id][stratum].append(accuracy)

    calibrations: List[NullPolicyCalibration] = []
    for policy_id, run in runs.items():
        current_hash = sha256_digest(
            [
                {"task_id": item.task_id, "prediction": item.prediction}
                for item in run.task_results
            ]
        )
        if current_hash != fixed_output_hashes[policy_id]:
            raise AssertionError("policy outputs changed during null calibration")
        for stratum in strata:
            task_ids = task_ids_by_stratum[stratum]
            observed = sum(
                predictions[policy_id][task_id] == task_by_id[task_id].gold_action
                for task_id in task_ids
            ) / len(task_ids)
            values = sorted(null_values[policy_id][stratum])
            percentile_index = max(0, math.ceil(0.95 * len(values)) - 1)
            null_p95 = values[percentile_index]
            calibrations.append(
                NullPolicyCalibration(
                    policy_id=policy_id,
                    partition=partition_name,
                    stratum=stratum,
                    permutations=permutations,
                    permutation_seed=permutation_seed,
                    fixed_output_hash=fixed_output_hashes[policy_id],
                    observed_accuracy=observed,
                    null_p95=null_p95,
                    exceeds_null=observed > null_p95,
                )
            )
    return calibrations


def write_artifacts(output: Path, dataset: BenchmarkDataset, partition: str) -> None:
    """Write canonical dataset and all deterministic baseline traces."""
    output.mkdir(parents=True, exist_ok=True)
    if partition != "sealed" and any(item.name == "sealed" for item in dataset.partitions):
        dataset = dataset.model_copy(
            update={
                "partitions": [
                    item for item in dataset.partitions if item.name != "sealed"
                ],
                "positional_leak_assertions": [
                    item
                    for item in dataset.positional_leak_assertions
                    if item.partition != "sealed"
                ],
            }
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
