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

## AMENDMENT 3 — A1–A6 superseded; re-expressed relative to chance (2026-08-11)

**Signed off by Darwin (ELL Lead)**, on Reviewer's insistence that this be explicit rather than
inherited from a leak fix. It is the largest amendment to this document and the reasoning is
recorded in full.

### What changed

Removing the action-namespace leak requires a shared rule-agnostic action vocabulary. That makes
off-rule evidence *usable* rather than inert, so null policies stop abstaining and the measurement
floor moves from ≈0 to ≈1/3.

Verified premise: all 24 development rules carry exactly 3 actions, and all 1,008 tasks present a
3-way choice — so chance is exactly `1/3`. Reviewer's simulation of the proposed remap gives 0.4196
for an aligned mapping and 0.3294 (≈ chance) for a per-rule randomised one. I verified the premise
myself; I have **not** independently reproduced those two simulated figures.

**Consequence:** A1's `[0.25, 0.45]` band no longer describes an intermediate comparator. Its lower
half sits below chance — a comparator at 0.30 would be indistinguishable from guessing.

### Ruling A — re-express, do not re-number

A1–A6 failed because raw accuracy bands are **floor-dependent**. Replacing one set of magic numbers
with another leaves the same defect. All comparator criteria are therefore restated in
**chance-normalised** form:

```
normalised = (observed - chance) / (ceiling - chance)
chance   = the rule-label-permuted empirical null (A9b), per stratum and partition
ceiling  = oracle-retrieval on the same stratum and partition
```

A criterion expressed this way survives any future floor or ceiling change, which is the third time
a floor assumption has broken a threshold in this document.

### Ruling B — the metric must distinguish abstention from error

Reviewer's strongest point: once abstention is no longer the default failure mode, the far stratum
stops separating "found the rule" from "guessed". No threshold can repair that — the **metric** has
to.

**Required:** the primary metric scores abstention strictly above a wrong answer. A policy that
guesses must do worse than one that declines. This restores discriminative power at far independently
of where the floor sits, and it is the correct expression of ELL's own principles — a system that
claims to represent uncertainty should not be rewarded for confident error.

### Ruling C — sequencing, to protect preregistration

New bands are preregistered **from the permuted null alone, before any real comparator numbers on
the repaired generator are examined**:

1. Land the leak repair (PR #7: round-robin interleaving + seed-committed randomised balanced action
   mapping).
2. Build A9 / A9b, including the permutation harness.
3. Compute the permuted null. **Look at nothing else.**
4. Preregister normalised bands for A1–A6 from that null.
5. Only then measure real comparators.

Inverting steps 4 and 5 would be fitting the target to the observation.

### Status of each criterion

| criterion | status |
|---|---|
| A1–A6 | **superseded**, pending normalised re-derivation at step 4 |
| A7 (chronology), A8 (determinism) | **unchanged and in force** — floor-independent |
| A9, A9b (leak battery) | **in force** |

### Guard against amendment drift

This is the third amendment, and I am the single point of failure for all three. Any further change
to A1–A6 requires: an a-priori derivation that does not consult policy results; independent review by
someone who did not author the change; and Danny's explicit sign-off. Recording this because
"it turned out to be a specification error" is an excuse that gets easier to reach for each time.

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
| A9 | **Null-policy leak battery** — per-record selection precision, every null policy, every stratum; **train + development** | `<= 2x 1/rule_count` |
| A9b | Null-policy **accuracy** vs its empirically calibrated leak-free null | within the simulated null's 95% interval |

## A9 — the null-policy leak battery (amendment, 2026-08-11)

Added on Reviewer's proposal, after the third distinct leak was found by measurement rather than
by reading code. The gold-`scope` shortcut, future-peek, and positional leakage were all caught by
someone happening to look. That is luck, and it does not scale to a sealed run.

A **null policy** carries no legitimate signal by construction. Required set:

- 5 uniformly random visible records;
- recency only (the 5 highest-sequence visible records);
- `record_id` sort order;
- the 5 lowest-sequence visible records;
- **`action-filter`** — select visible records whose `observed_action` is in `task.allowed_actions`
  (added 2026-08-11; this policy reads no text, uses no position, touches no gold field, and scored
  1.0000 same-rule precision with 0.7143 far accuracy).

**No null policy may exceed chance on any stratum.** Any null policy that beats chance is a leak
somewhere, by definition.

### Sealed boundary — corrected 2026-08-11

The first draft of A9 said "every partition" while this document's own scope line says sealed is
never opened. That was a contradiction I introduced, caught by Forge before it reached CI. Scoring
null-policy *accuracy* on sealed requires reading sealed `gold_action` and `transfer` on every CI
run, which would have broken the seal continuously.

The distinction that resolves it: the sealed boundary exists to stop policies seeing sealed answers,
and to stop humans tuning against sealed performance. So:

| check | reads | where it runs |
|---|---|---|
| **structural** — recent-tail rule concentration | `rule_id`, `sequence`; no gold answers, no scoring | train + development every CI run; sealed **once at generation**, asserted into the sealed manifest |
| **null-policy accuracy** | `gold_action`, `transfer` | train + development only |
| the same battery on sealed | gold | **exactly once**, inside the confirmatory study, after opening |

A structural invariant about the generator's layout is a property of the data, reveals nothing a
policy could exploit, and no tuning decision follows from it. A null-policy *score* is a performance
signal that someone would act on — that is what must not be readable before opening.

Because generation is deterministic from the seed, structural soundness demonstrated on train and
development is evidence about the layout *algorithm*, which is the same algorithm that produces
sealed. The one-time sealed assertion at generation closes the remaining gap without a repeated read.

### Chance model — corrected 2026-08-11

My first A9 draft applied `2x 1/rule_count` to null-policy **accuracy**. That chance model is wrong
for its own retrieval budget. Each null policy selects **5** records, so under leak-free independent
mixing the probability that at least one selected record shares the task's rule is
`1 - (1 - 1/r)^5`, not `1/r`:

| partition | rules | per-record chance | P(>=1 same-rule in 5) | my original bound |
|---|---:|---:|---:|---:|
| train | 12 | 8.33% | **35.3%** | 16.7% |
| development | 24 | 4.17% | **19.2%** | 8.3% |
| sealed | 54 | 1.85% | **8.9%** | 3.7% |

The original bound sat *below* the legitimate five-draw exposure at every tier. A9 would therefore
have reported leak-free behaviour as a leak — false positives blocking real work, which is the
mirror image of the failure it was written to prevent. Measured combined development null accuracy
is 7.7%–16.4%: above my bound, below the 19.2% exposure, and **not** evidence of a leak.

Corrected split:

- **A9 (the leak test)** compares **per-record selection precision** to `1/r`. This is the clean
  test: it is invariant to retrieval budget and to the answer stage. The structural invariant
  already passes exactly here — 8.33% / 4.17% / 1.85%.
- **A9b** covers null-policy *accuracy*, which is jointly determined by five draws, the answer
  stage and the action state, so it has no clean analytic bound. It is compared to an
  **empirically calibrated leak-free null** — simulate the null by randomising rule assignment
  under leak-free mixing and require the observed value inside that interval. The **method** is
  pre-committed; the number is not, because the answer stage is still changing.

### The principle behind all four leaks: fields are not information

Four distinct leaks have now been found — the gold-`scope` shortcut, future-peek, positional
layout, and the action-namespace join. **Not one of them was an illegitimate field.** Each was a
join or correlation between fields that are individually defensible:

| leak | the join |
|---|---|
| gold-`scope` | `scope` was literally the rule label |
| future-peek | legitimate fields, read at an illegitimate time |
| positional | `sequence` correlated with `rule_id` via block layout |
| action-namespace | `allowed_actions` x `observed_action` fingerprints the rule exactly |

The boundary certified in PR #5 was a **field-level** boundary: no gold or generator field reaches
an eligible policy. That certification was correct and still is. It simply does not imply what we
were treating it as implying — that no *rule information* reaches a policy.

**Requirement:** the boundary is specified in terms of information about `rule_id`, not a field
allowlist. Any field reachable by a policy must be shown to carry no rule information *in
combination with every other permitted field*. Since that cannot be proven by inspection — all four
leaks survived code review and were caught by measurement — the null-policy battery is the
operational proxy, and it must run continuously rather than per-review.

### Known construct limitation, to be resolved in v0.8

Collapsing the action namespace to an opaque shared pair removes the exact rule join. It also makes
explicit that the current deterministic answer stage grades **evidence selection** far more than
semantic action inference. That is a real narrowing of what the benchmark measures, and it bounds
what a "supported" verdict could claim: support for better evidence selection, not for better
decisions in the fuller sense.

This is recorded rather than resolved. It is the same tension as the earlier text-only ruling, which
failed because the generator provides no lexical bridge between record text and action labels. The
honest position is that Phase 1-2 measure governed retrieval quality under a frozen decision rule;
claims about decision quality require the v0.8 answer-stage design question to be settled first.

### Is this a relaxation? No — and here is the test

Changing a pre-committed threshold is exactly what this document exists to prevent, so the
distinction has to be stated rather than assumed.

**Legitimate:** the specification was mathematically wrong under a leak-free null, and the error is
derivable *a priori* from the retrieval budget and rule count without consulting any policy's
results. That is the case here — the five-draw exposure is arithmetic, not an observation.

**Illegitimate:** a threshold is unmet, the results disappoint, and the number moves.

A1–A6 remain untouched, including the ones currently failing. That is the difference: A1 stayed at
`[0.25, 0.45]` when it was inconvenient, and A9's chance model changed when it was wrong. Any future
amendment must state which of the two cases it is, with the derivation.

Threshold is **parameterised by the tier's own rule count**, not a constant — chance differs per
tier and a constant would pass falsely on sealed while failing spuriously on train:

| partition | rules | chance | A9 bound (2x) |
|---|---:|---:|---:|
| train | 12 | 8.33% | 16.7% |
| development | 24 | 4.17% | 8.3% |
| sealed | 54 | 1.85% | 3.7% |

Runs on every CI invocation, so the fourth leak is caught by the harness rather than by a reviewer
who happens to look. Note the generator's rule counts (12/24/54) also differ from v0.7's declared
8/16/36 — another instance of the generator matching neither contract.

### Related: positional leakage is a sixth adversarial condition

The five recovered detectors (R4) do not cover it. Recorded as a required condition:
**`positional-leakage`** — stream position must carry no information about the latent rule.
Regression: recent-tail rule concentration at or near `1 / rule_count`, asserted per partition.

Measured before the fix, on `6724949`: **4968/5037 (98.6%)** of each task's five most recent
visible records belonged to that task's own rule, against a 4.17% chance baseline on development.
Independently reproduced by Darwin and Reviewer.

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
