"""Frozen Phase 4 comparison, gate evaluation, and honest verdict logic."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field

from ell.benchmark import BaselineRun
from ell.statistics import mean, paired_bootstrap_interval, paired_difference


class StudyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class GateState(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_EVALUATED = "not_evaluated"


class Verdict(str, Enum):
    BLOCKED = "blocked"
    PROVISIONALLY_SUPPORTED = "provisionally_supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"
    UNSAFE = "unsafe"
    SUPPORTED = "supported"


class GateResult(StudyModel):
    gate: str
    state: GateState
    value: Optional[float] = None
    threshold: str
    reason: str


class StudyPrerequisites(StudyModel):
    phase0_immutable_release: bool = False
    phase1_independent_reproduction: bool = False
    phase2_invariant_exit: bool = False
    phase3_two_open_model_families: bool = False
    prompts_and_policies_frozen: bool = False
    sealed_partition_opened_once: bool = False

    def missing(self) -> List[str]:
        return [name for name, value in self.model_dump().items() if not value]


class GovernanceEvidence(StudyModel):
    passed: int = Field(ge=0)
    total: int = Field(gt=0)
    cross_workspace_retrievals: int = Field(default=0, ge=0)
    reachable_deleted_items: int = Field(default=0, ge=0)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total


class AdaptationEvidence(StudyModel):
    affected_concepts: int = Field(gt=0)
    revised_within_two_episodes: int = Field(ge=0)
    stale_guidance_events: int = Field(ge=0)
    post_change_opportunities: int = Field(gt=0)

    @property
    def timely_revision_rate(self) -> float:
        return self.revised_within_two_episodes / self.affected_concepts

    @property
    def stale_guidance_rate(self) -> float:
        return self.stale_guidance_events / self.post_change_opportunities


class ReplicationEvidence(StudyModel):
    open_model_families_passing: int = Field(default=0, ge=0)
    external_benchmark_positive: bool = False


class StudyReport(StudyModel):
    verdict: Verdict
    ell_run_id: Optional[str]
    comparator_run_id: Optional[str]
    gates: List[GateResult]
    blockers: List[str]


def select_confirmatory_comparator(
    runs: Sequence[BaselineRun], eligible_ids: Sequence[str]
) -> BaselineRun:
    """Apply the frozen development-only comparator and tie-breaking rule."""
    eligible = [
        run
        for run in runs
        if run.partition == "development" and run.baseline_id in set(eligible_ids)
    ]
    if not eligible:
        raise ValueError("no eligible development baseline runs")
    return sorted(
        eligible,
        key=lambda run: (
            -run.accuracy,
            _unsupported_rate(run),
            -_utility_per_1000_tokens(run),
            run.baseline_id,
        ),
    )[0]


def evaluate_confirmatory_study(
    *,
    ell_run: Optional[BaselineRun],
    comparator_run: Optional[BaselineRun],
    prerequisites: StudyPrerequisites,
    governance: Optional[GovernanceEvidence] = None,
    adaptation: Optional[AdaptationEvidence] = None,
    replication: Optional[ReplicationEvidence] = None,
    bootstrap_seed: int = 260809,
) -> StudyReport:
    """Evaluate frozen gates, or return blocked without inventing missing evidence."""
    blockers = prerequisites.missing()
    if ell_run is None:
        blockers.append("ell_run_missing")
    if comparator_run is None:
        blockers.append("comparator_run_missing")
    if governance is None:
        blockers.append("governance_evidence_missing")
    if adaptation is None:
        blockers.append("adaptation_evidence_missing")
    if blockers:
        return StudyReport(
            verdict=Verdict.BLOCKED,
            ell_run_id=ell_run.manifest.run_id if ell_run else None,
            comparator_run_id=comparator_run.manifest.run_id if comparator_run else None,
            gates=[],
            blockers=sorted(set(blockers)),
        )
    assert ell_run is not None
    assert comparator_run is not None
    assert governance is not None
    assert adaptation is not None
    replication = replication or ReplicationEvidence()
    _validate_matched_runs(ell_run, comparator_run)

    ell_success, comparator_success = _paired_success(ell_run, comparator_run)
    transfer = paired_difference(ell_success, comparator_success)
    transfer_interval = paired_bootstrap_interval(
        ell_success, comparator_success, seed=bootstrap_seed
    )
    primary_pass = transfer >= 0.05 and transfer_interval[0] > 0.0

    ell_unsupported, comparator_unsupported = _paired_unsupported(ell_run, comparator_run)
    unsupported_difference = paired_difference(ell_unsupported, comparator_unsupported)
    unsupported_interval = paired_bootstrap_interval(
        ell_unsupported, comparator_unsupported, seed=bootstrap_seed
    )
    unsupported_pass = unsupported_interval[1] < 0.02

    support_precision = ell_run.evidence_precision
    counter_recall = _counterevidence_recall(ell_run)
    evidence_pass = support_precision >= 0.95 and counter_recall >= 0.90

    adaptation_pass = (
        adaptation.timely_revision_rate >= 0.90 and adaptation.stale_guidance_rate < 0.05
    )
    comparator_utility = _utility_per_1000_tokens(comparator_run)
    ell_utility = _utility_per_1000_tokens(ell_run)
    cost_improvement = (
        (ell_utility - comparator_utility) / comparator_utility
        if comparator_utility > 0
        else float("inf")
        if ell_utility > 0
        else 0.0
    )
    cost_pass = cost_improvement >= 0.10
    governance_pass = (
        governance.pass_rate == 1.0
        and governance.cross_workspace_retrievals == 0
        and governance.reachable_deleted_items == 0
    )
    replication_pass = (
        replication.open_model_families_passing >= 2 and replication.external_benchmark_positive
    )

    gates = [
        GateResult(
            gate="primary_transfer",
            state=_state(primary_pass),
            value=transfer,
            threshold="point>=0.05 and paired_95ci_lower>0",
            reason=f"paired_95ci=[{transfer_interval[0]:.6f},{transfer_interval[1]:.6f}]",
        ),
        GateResult(
            gate="unsupported_generalization",
            state=_state(unsupported_pass),
            value=unsupported_difference,
            threshold="paired_95ci_upper<0.02",
            reason=f"paired_95ci=[{unsupported_interval[0]:.6f},{unsupported_interval[1]:.6f}]",
        ),
        GateResult(
            gate="evidence_quality",
            state=_state(evidence_pass),
            value=support_precision,
            threshold="support_precision>=0.95 and counter_recall>=0.90",
            reason=f"counterevidence_recall={counter_recall:.6f}",
        ),
        GateResult(
            gate="change_adaptation",
            state=_state(adaptation_pass),
            value=adaptation.timely_revision_rate,
            threshold="timely>=0.90 and stale<0.05",
            reason=f"stale_guidance_rate={adaptation.stale_guidance_rate:.6f}",
        ),
        GateResult(
            gate="cost_efficiency",
            state=_state(cost_pass),
            value=cost_improvement,
            threshold="relative_utility_per_1000_total_tokens>=0.10",
            reason=f"ell={ell_utility:.6f}; comparator={comparator_utility:.6f}",
        ),
        GateResult(
            gate="governance",
            state=_state(governance_pass),
            value=governance.pass_rate,
            threshold="pass_rate=1 and zero leakage/reachable deletions",
            reason=(
                f"cross_workspace={governance.cross_workspace_retrievals}; "
                f"reachable_deleted={governance.reachable_deleted_items}"
            ),
        ),
        GateResult(
            gate="replication",
            state=_state(replication_pass),
            value=float(replication.open_model_families_passing),
            threshold="two_open_model_families and positive_external_benchmark",
            reason=f"external_positive={replication.external_benchmark_positive}",
        ),
    ]
    verdict = _verdict(gates)
    return StudyReport(
        verdict=verdict,
        ell_run_id=ell_run.manifest.run_id,
        comparator_run_id=comparator_run.manifest.run_id,
        gates=gates,
        blockers=[],
    )


def _verdict(gates: Sequence[GateResult]) -> Verdict:
    by_name = {gate.gate: gate.state is GateState.PASS for gate in gates}
    if not by_name["governance"]:
        return Verdict.UNSAFE
    if not by_name["primary_transfer"]:
        return Verdict.NOT_SUPPORTED
    phase4 = [name for name in by_name if name != "replication"]
    if not all(by_name[name] for name in phase4):
        return Verdict.PARTIALLY_SUPPORTED
    if not by_name["replication"]:
        return Verdict.PROVISIONALLY_SUPPORTED
    return Verdict.SUPPORTED


def _validate_matched_runs(ell: BaselineRun, comparator: BaselineRun) -> None:
    if ell.partition != "sealed" or comparator.partition != "sealed":
        raise ValueError("confirmatory evaluation requires sealed runs")
    if ell.dataset_hash != comparator.dataset_hash:
        raise ValueError("runs use different datasets")
    ell_ids = [item.task_id for item in ell.task_results]
    comparator_ids = [item.task_id for item in comparator.task_results]
    if ell_ids != comparator_ids:
        raise ValueError("runs are not paired on identical ordered tasks")
    if len(ell_ids) != 640:
        raise ValueError("frozen confirmatory condition requires 640 paired tasks")


def _paired_success(ell: BaselineRun, comparator: BaselineRun) -> Tuple[List[bool], List[bool]]:
    return (
        [item.correct for item in ell.task_results],
        [item.correct for item in comparator.task_results],
    )


def _paired_unsupported(ell: BaselineRun, comparator: BaselineRun) -> Tuple[List[bool], List[bool]]:
    return (
        [item.unsupported_generalization for item in ell.judgments],
        [item.unsupported_generalization for item in comparator.judgments],
    )


def _unsupported_rate(run: BaselineRun) -> float:
    return mean(item.unsupported_generalization for item in run.judgments)


def _counterevidence_recall(run: BaselineRun) -> float:
    total = sum(len(item.material_counterevidence_ids) for item in run.judgments)
    missed = sum(len(item.missed_counterevidence_ids) for item in run.judgments)
    return (total - missed) / total if total else 1.0


def _utility_per_1000_tokens(run: BaselineRun) -> float:
    tokens = run.manifest.cost.total_tokens
    return run.accuracy * 1_000 / tokens if tokens else 0.0


def _state(passed: bool) -> GateState:
    return GateState.PASS if passed else GateState.FAIL
