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

## Finding: the seed varies surface text, not structure — the seal is weaker than assumed

Not a leak, so nothing in the A9 battery catches it. Found by Reviewer while checking Scholar's
uncertainty model; reproduced independently by Darwin at `192/336` = **4/7** across seeds
1729, 11, 42, 101 and 777, sd **0.0000**. Reviewer measured 8 seeds in both orderings: 4/7 source,
6/7 recency, zero variance throughout.

Cause is the template's modular cadence — `is_exception = index % 11 == 10`,
`is_contradiction = index % 7 == 6`, `stratum = task_index % 3` — all independent of the seed.

Consequences: `oracle-retrieval` is a **constant**, so no confidence-interval reasoning applies to it;
same-seed reproduction verifies determinism only, which means Phase 1's clean-machine exit criterion
was always trivially satisfiable and is not evidence of generalisation; development and sealed are
**structurally the same dataset at different scale**, so anything tuned against development structure
is tuned against sealed structure with no sealed-run discipline able to detect it; and between-rule SD
estimated on development understates the truth, which is what v0.8 sizing depends on.

This is a deeper problem than any of the four leaks — the seal is the project's core protection.

**Rulings:** structure is sampled per seed rather than fixed; the sealed partition is drawn with
structural parameters independent of development; A8 same-seed byte-identity is retained as a
determinism check but explicitly demoted from evidence of robustness; new criterion **A11** requires
non-zero between-seed variance so a constant fails loudly instead of reading as precision.

## Finding: the answer stage is order-sensitive — a construct threat to the primary estimand

Recorded as a finding in its own right, separately from the withdrawn stop below, because it outlives
that fix. Discovered while checking an unrelated claim.

With **identical** gold evidence, changing only presentation order moves `oracle-retrieval` on far
from **0.5714** (generator source order) to **0.8482** (recency order) — 28 points. `sequence` is
policy-visible and any sane retriever ranks by recency, so source order understates the ceiling by
construction.

The consequence reaches past the oracle. If the answer stage is that order-sensitive, then "ELL minus
strongest comparator" partly measures how each system happens to *order* its output rather than what
it knows: two systems with identical retrieval and identical concepts could differ by tens of points
on emission order alone. No leak repair touches this. `retrieval_weight = score / (rank + 1)` is
therefore a substantive modelling decision, not a frozen implementation detail.

**Rulings.** The oracle presents evidence in the best order derivable from policy-visible fields —
descending `sequence`; generator emission order is not a ranking. Pinned *before* re-measurement so
the ceiling is not chosen to fit the threshold. New criterion **A10**: the frozen answer stage must be
order-invariant given a fixed evidence set. Recency enters as an **explicit feature** (record time
relative to the task), never implicitly through list position — which preserves legitimate recency
information while making the ceiling independent of presentation.

## ~~Outcome: Phase 1 stop~~ — RETRACTED same day (2026-08-11)

The revision sequence terminated in a stop rather than a green instrument. Measuring floor and
ceiling only — eligible commitment `de1d0be9…` unopened — gave a far corridor of **0.0476**
(`oracle-retrieval` 0.5714 minus max permuted-null p95 0.5238) against a preregistered primary effect
of **0.0500**. The admissible band is empty before any separation margin, so A1–A6 cannot be
recalibrated on the current answer space. See the stop record in
`INSTRUMENT_ACCEPTANCE_PRECOMMIT.md`.

**Retracted the same day.** The ceiling input (0.5714) had already been labelled invalid by Forge on
`6724949` and was never repaired; recency ordering moves it to 0.8482, which turns a −0.0024 shortfall
into +0.2744 of admissible headroom. Scholar separately showed the 0.0024 margin is only **0.088 SE**
at development-far N=336, so emptiness was never established even on the original number. The
retraction covers both the point-estimate arithmetic and the sampling-robust power version, since both
take the same defective ceiling as input.

Standing requirement from this episode: a stop result is the strongest claim this project can make
about itself, and it may not rest on an input anyone has already called broken, nor on point estimates
inside their own sampling error.

This was in any case a finding about the instrument, not about ELL. H1–H7 remain untested.

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
