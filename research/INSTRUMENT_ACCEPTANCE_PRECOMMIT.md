# Instrument acceptance criteria — pre-commitment

**Status:** pre-committed before repair. **Date:** 2026-08-11. **Owner:** Darwin (ELL Lead).
**Committed at:** `f8ad71c9a59a36a6970c803d3eaea5de1302b082`, before any repair work begins.

## Why this document exists before the repair, not after

The instrument is currently unable to grade ELL. Repairing it while free to choose the pass
condition afterwards is p-hacking the instrument — in a project whose entire credibility rests on
preregistration. Adopted on Reviewer's insistence; the objection was correct.

These numbers are fixed now. **If the repaired instrument cannot meet them, that is a finding
about the benchmark design.** It is not a reason to relax the numbers. The permitted responses are
to redesign task difficulty, or to report that the benchmark cannot grade the hypothesis. Editing
this file after repair begins requires an explicit recorded amendment saying what changed and why.

## Ruling 1 — the benchmark must measure a decision, not a lookup

`_predict` (`src/ell/benchmark.py:656`) computes the answer as a weighted vote over
`record.action`, `record.outcome` and `record.relation` — generator fields. No policy infers an
action from text; the answer is stapled to each retrieved record. The benchmark therefore measures
**selection only**, with a gold aggregator standing in for the answer model.

That cannot test ELL's hypothesis. ELL claims revisable, evidence-grounded concepts improve
**decisions** on structurally distant situations. A harness that hands the answer to whoever
retrieves the right row tests retrieval.

**Ruling:** introduce a **frozen deterministic answer stage**, shared bit-identically by every
condition, that infers the action from record **text only**. `action`, `outcome`, `relation`,
`rule_id`, `scope` and all gold fields become evaluator-only and unreachable by the answer stage.

This keeps Phases 1–2 free of any LLM — the answer stage is deterministic and frozen, not
model-generated. It is the matched answer stage Forge proposed, with the visibility boundary made
explicit.

**Corollary:** the answer stage must be able to act on exception records. Today `_predict` skips
them, so selecting an exception can never change the answer while the safety metric fires on
having selected it — the gate is cosmetic. After the repair, exception handling must be
behavioural: selecting an exception record must be capable of changing the emitted action.

## Ruling 2 — chronology is a runner invariant, not a policy courtesy

No selector or answer stage may observe a record with `sequence >= task.sequence`, nor an outcome
with `outcome_observed_time > task.observed_time`. Enforced by the runner at projection time,
before any selector executes. This is requirement R5.

## Pre-committed pass conditions

Measured on the **development** partition only. Sealed is not opened for any of this.

| # | criterion | threshold |
|---|---|---|
| A1 | At least one **eligible non-oracle** comparator on the primary (far) stratum | in `[0.25, 0.45]` |
| A2 | Pairwise separation of eligible comparators on far | no two within `0.02` absolute |
| A3 | Information ceiling is real: `maximum-context` vs `no-memory` on far | `>= +0.05` |
| A4 | A **known-good non-oracle** control, reading zero evaluator-only fields, on far | `>= 0.60` |
| A5 | Strict ordering on **every** stratum: broken `<` eligible intermediate `<` `oracle-retrieval` `<=` `oracle-concept` | strict where stated |
| A6 | Near stratum is not saturated: `oracle-retrieval` minus best eligible on near | `>= 0.10` |
| A7 | Chronology violations across all conditions | exactly `0`, test-asserted |
| A8 | Two full runs from the same seed | byte-identical artifacts |

Rationale for A1: a comparator floored near `0.004` makes a +5-point win recoverable by
identifying ~6% of latent rules, which would make a "supported" verdict close to uninformative. A
comparator in the mid-range makes the primary gate demanding. This is the falsification test
Reviewer named — if far can be lifted into that band, the main criticism of the gate design
dissolves; if it cannot, the stratum definition is wrong.

Rationale for A4: `direct-insight`'s historical `1.0` was not a valid control — it matched on
`scope`, which *was* the latent rule label. A control that reads no evaluator-only field and still
performs well is the only evidence that the task is learnable from permitted evidence at all. If
no such policy can be built, the benchmark is unsolvable-by-construction and must be redesigned.

Rationale for A6: `near` currently sits at `0.5714` for retrieval *and* for `oracle-retrieval`
simultaneously. A stratum where the comparator already equals its own ceiling cannot grade
anything.

## Sizing is deliberately absent

No tier counts, no rule counts, no discordance rate appear above. Those are **empirical outputs**
of the repaired instrument, not inputs:

```
chronology filter + policy boundary + answer stage
  -> comparators differentiate
    -> between-rule SD and discordance estimable on development
      -> required rule count determinate
        -> v0.8 tiers written -> freeze -> Phase 3
```

v0.7 declares 36 sealed rules while its own `cluster_power` requires 117 at between-rule SD 0.15
and 208 at 0.20. Writing any tier count before A1–A8 hold would preregister a number we cannot
support.

## Order of work

1. CI job running the full suite — **before** the repair. A repair verified by a suite nobody runs
   automatically is how this state arose.
2. This pre-commitment (done).
3. Repair: chronology filter, loader boundary, answer stage, the three missing detectors.
4. Re-measure against A1–A8.
5. Estimate between-rule SD and discordance on development.
6. Write v0.8 with sizing derived from step 5.
7. Publication reconciliation, immutable tag, then Phase 3.

## Measured-before state, for comparison

Recorded so the repair's effect is visible. **These numbers were taken on a runner that leaks
future evidence and are unsafe as a baseline** — retained only to show direction of change.

| condition | far | near |
|---|---|---|
| bm25 / exact-vector / fused-retrieval | 0.0040 | 0.5714 |
| direct-insight | 0.0040 | 0.5655 |
| rolling-summary | 0.0179 | 0.0179 |
| oracle-retrieval | 0.5714 | 0.5714 |
| oracle-concept | 0.9524 | 0.9524 |

Full suite at the same commit: 5 failed, 28 passed.
