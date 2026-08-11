from __future__ import annotations

import pytest

from ell.benchmark import BASELINES, generate_dataset, run_baseline
from ell.study import (
    StudyPrerequisites,
    Verdict,
    evaluate_confirmatory_study,
    select_confirmatory_comparator,
)


def test_current_study_state_is_blocked_without_opening_sealed_data() -> None:
    report = evaluate_confirmatory_study(
        ell_run=None,
        comparator_run=None,
        prerequisites=StudyPrerequisites(),
    )
    assert report.verdict is Verdict.BLOCKED
    assert "phase3_two_open_model_families" in report.blockers
    assert "sealed_partition_opened_once" in report.blockers
    assert report.gates == []


def test_comparator_selection_uses_development_only_and_frozen_ties() -> None:
    dataset = generate_dataset(1729, 481516)
    runs = [run_baseline(dataset, "development", baseline_id) for baseline_id in BASELINES]
    comparator = select_confirmatory_comparator(
        runs,
        ["bm25", "exact-vector", "fused-retrieval", "rolling-summary", "direct-insight"],
    )
    eligible = {
        "bm25", "exact-vector", "fused-retrieval", "rolling-summary", "direct-insight"
    }
    assert comparator.baseline_id in eligible
    assert comparator.accuracy == max(run.accuracy for run in runs if run.baseline_id in eligible)
    assert comparator.partition == "development"


def test_confirmatory_evaluation_rejects_development_runs() -> None:
    dataset = generate_dataset(1729, 481516)
    run = run_baseline(dataset, "development", "direct-insight")
    complete = StudyPrerequisites(
        phase0_immutable_release=True,
        phase1_independent_reproduction=True,
        phase2_invariant_exit=True,
        phase3_two_open_model_families=True,
        prompts_and_policies_frozen=True,
        sealed_partition_opened_once=True,
    )
    from ell.study import AdaptationEvidence, GovernanceEvidence

    with pytest.raises(ValueError, match="sealed runs"):
        evaluate_confirmatory_study(
            ell_run=run,
            comparator_run=run,
            prerequisites=complete,
            governance=GovernanceEvidence(passed=10, total=10),
            adaptation=AdaptationEvidence(
                affected_concepts=10,
                revised_within_two_episodes=10,
                stale_guidance_events=0,
                post_change_opportunities=10,
            ),
        )
