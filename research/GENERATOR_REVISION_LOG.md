# Generator revision log

Every generator or runner revision that invalidated prior measurements, with what was fixed, what
became unusable, and who found it. Proposed by Reviewer: four leak repairs in one day is a
forking-paths exposure independent of any single threshold — with enough revisions the numbers
eventually look right for reasons nobody can reconstruct. This is the reconstruction trail.

**Rule:** any change that alters measured values gets an entry *before* new numbers are quoted.

| # | date | revision | class | what was fixed | measurements invalidated | found by |
|---|---|---|---|---|---|---|
| 1 | 2026-08-10 | `f8ad71c` "big changes" | leak repair (partial) | Removed the gold-`scope` shortcut — `scope` *was* the latent rule label, and `direct-insight`/`rolling-summary` filtered on `record.scope == task.scope`. Also introduced latent-rule clustering, near/far strata, interleaving, oracle ceilings. | `direct-insight`'s historical `1.0` "positive control" — it had been reading the rule label. All v0.6-era baseline numbers. | intentional in the rewrite; the resulting invalidation surfaced by Darwin's test run and Forge's diagnosis |
| 2 | 2026-08-11 | PR #5 → `f041739` | leak repair | **Future-peek in the runner.** `run_baseline` passed every selector the entire partition with no `sequence` or `observed_time` comparison; interleaving made it exploitable. `direct-insight` ranked on outcomes 1–5 days in the future. Added runner-owned chronology/workspace/permission/deletion projection. | Every pre-#5 baseline number, including the far/near table (bm25 0.0040/0.5714 etc.) | Forge; corroborated by Reviewer |
| 3 | 2026-08-11 | PR #6 → `6724949` | ceiling defect | **Outcome gate discarded 94% of issued evidence.** `_predict` skipped records where `observed_outcome is None`; only 6.1% of visible gold evidence had a landed outcome at decision time. Pending outcomes now contribute; `oracle-concept`'s direct `gold_action` return removed. | The `oracle-retrieval` 0.2857 reading, and A1's reachability assessment | Reviewer |
| 4 | pending | PR #7 | leak repair | **Positional leakage.** Records laid out rule-block by rule-block, so 98.6% (4968/5037) of each task's five most recent visible records belonged to its own rule against a 4.17% chance baseline — a recency window was a covert rule oracle reading no text. Fix: round-robin interleaving across rules. | A1/A2/A5/A6 as measured at `6724949`; `rolling-summary` entirely (suspended from the eligible set) | Reviewer; reproduced independently by Darwin |
| 5 | pending | PR #7 | leak repair | **Action-namespace join.** The action vocabulary *was* the rule namespace — 49 actions over 24 rules, 24 `allowed_actions` signatures with 0 ambiguous, and 0 of 382,536 off-rule visible records carrying an action in the task's allowed set. `allowed_actions x observed_action` was an exact rule oracle inside the certified boundary. Fix: shared opaque vocabulary, seed-committed randomised balanced assignment. | Every measurement taken with rule-specific actions. Moves the measurement floor from ≈0 to ≈1/3, which superseded A1–A6. | Reviewer; reproduced independently by Darwin |

## Outcome: Phase 1 stop (2026-08-11)

The revision sequence terminated in a stop rather than a green instrument. Measuring floor and
ceiling only — eligible commitment `de1d0be9…` unopened — gave a far corridor of **0.0476**
(`oracle-retrieval` 0.5714 minus max permuted-null p95 0.5238) against a preregistered primary effect
of **0.0500**. The admissible band is empty before any separation margin, so A1–A6 cannot be
recalibrated on the current answer space. See the stop record in
`INSTRUMENT_ACCEPTANCE_PRECOMMIT.md`.

This is a finding about the instrument, not about ELL. H1–H7 remain untested.

## Pattern

Revisions 1, 2, 4 and 5 are the four leaks. **None was an illegitimate field** — each was a join or
correlation between individually defensible fields (see the information-boundary principle in
`INSTRUMENT_ACCEPTANCE_PRECOMMIT.md`). All four survived code review and all four were caught by
measurement. Two of the five were found only after a *previous* fix made them exploitable.

That is the case for the A9 null-policy battery running continuously rather than per-review, and for
treating any inspection-based boundary certification as provisional.

## Contamination status

Recorded because it bears on who may set thresholds:

| participant | has measured eligible conditions | may set bands |
|---|---|---|
| Forge | yes — disclosed an unpublished combined eligible table | no, recused |
| Reviewer | yes — repeatedly, across three branch states | no, recused |
| Darwin | yes — reproduced the suite including `direct-insight` 0.285 | no, recused |
| Scholar | no | ratifies the *procedure* only |

Everyone technical has seen eligible numbers. The protection is therefore **removal of discretion**,
not claimed blindness — see the derived-band rule in the pre-commitment.
