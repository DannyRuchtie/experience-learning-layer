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

## ~~PHASE 1 STOP~~ — RETRACTED 2026-08-11, same day

> **RETRACTED by Darwin (ELL Lead), on Reviewer's objection. Do not cite this section as a stop
> result.**
>
> The declaration rests on `oracle-retrieval = 0.5714`, a ceiling **Forge had already labelled
> invalid** on `6724949` — "the oracle supplies current evidence plus stale counterevidence in source
> order… it is not a valid information ceiling yet" — and which was never repaired. Changing only the
> presentation order from source to recency, with identical gold evidence, moves the far oracle from
> **0.5714 to 0.8482**. Redone at 0.8482 the upper edge is `0.7982` against a null p95 of `0.5238`,
> giving **0.274** of headroom. The band is wide, not empty.
>
> I verified the arithmetic but not the validity of its input. A stop result is the strongest claim
> this project can make about itself, and it must rest on a ceiling nobody has already called broken.
>
> **My causal attribution was also wrong.** I titled this "the two-action instrument cannot support
> the estimand". That does not follow: at k=2 a perfect answer stage scores 1.0 against a 0.5 floor —
> 0.5 of headroom. `oracle-concept` scores 1.0000 on the same instrument where `oracle-retrieval`
> scores 0.5714. The empty band was an **answer-stage failure**, localised by exactly that gap, and
> raising `k` alone would not have fixed it. I conflated the action-space limitation with the cause of
> the empty band; they are separate problems.
>
> Outstanding before the band can be re-tested: the ordering comparison must be re-run on the
> **combined** tree. Reviewer measured on `6d11f0c`, which still carries the two-argument `_predict`
> and lacks the pending-outcome repair, so oracle far reproduces 0.5714 there possibly by a different
> route.
>
> **Order:** repair the oracle ordering → re-measure floor and ceiling on the combined tree → re-test
> the band. If it is still empty then, the stop is real.
>
> **The retraction extends to the sampling-robust version of the argument.** Scholar independently
> reached an impossibility via power analysis rather than point estimates. That argument also takes
> `oracle-retrieval = 0.5714` as its input, so it falls with the same defect. Nobody re-establishes
> this stop on the same broken ceiling via better statistics.
>
> **Scholar's statistical correction, adopted as a standing requirement.** `0.0476 < 0.0500` does not
> establish an empty interval. Verified: development far N = 1008/3 = **336**; the three values are
> exactly `192/336`, `176/336`, `170/336`; SE ≈ **0.0272**; the 0.0024 margin is **0.088 SE** — a
> near-miss on one draw. **No stop claim may be recorded from point estimates.** It must be
> sampling-robust, stated at the *favourable* end of the ceiling interval, with the N requirement
> recomputed in `ell.statistics` rather than an order-of-magnitude heuristic. Decimals do not transfer
> from development (N=336) to sealed (N=1,512); the structural claim may.
>
> **Two aggregator points, recorded so they are not read as choosing the emptiest band:**
> `max` over null policies is **forced, not chosen** — matching a null to a comparator's abstention
> rate would require an eligible measurement. And `oracle-concept` is **not a ceiling** for any policy
> that must infer an action: it sets `prediction = task.gold_action` directly (`benchmark.py:617`), so
> its 1.0000 is definitional. `oracle-retrieval` — perfect evidence through the shared `_predict`
> stage — is the only real ceiling. `ELIGIBLE_COMPARATORS` excludes both oracles by contract, not by
> convention.
>
> **Still standing, for the right reason:** the v0.8 action-space ruling. Large shared `k` plus a
> semantic bridge remains the destination, and k=2 still bounds what a positive result could mean.
> That is an interpretation limit, not the cause of this arithmetic.
>
> A deeper point this exposes: the answer stage is **order-sensitive** given a fixed evidence set.
> That is a defect in its own right — it makes "the ceiling" a function of an arbitrary presentation
> choice. A frozen answer stage should be order-invariant given the same evidence, or the oracle must
> be defined at the best legitimate ordering. Until one of those holds, no ceiling figure is
> well-defined.

**Original declaration, retained for the record — superseded by the retraction above.** Measured by
Forge from floor and ceiling only, with the eligible commitment `de1d0be9…` unopened. Arithmetic
verified independently by Darwin.

| quantity | value |
|---|---|
| `oracle-retrieval` far ceiling | 0.5714 |
| max permuted-null p95 across null policies (far) | 0.5238 |
| available corridor | **0.0476** |
| preregistered primary effect that must fit below the ceiling | **0.0500** |

A valid band requires `null_p95 + X < comparator <= ceiling - effect`. At **X = 0**:

```
upper admissible bound = 0.5714 - 0.0500 = 0.5214
lower admissible bound = 0.5238
shortfall              = +0.0024   (must be negative)
```

**The admissible band is empty before any statistical-separation margin is applied.** The instrument
cannot simultaneously distinguish a comparator from null and leave room for the claimed +5-point
effect.

### This is a stop, not a tuning problem

Per this document's own terms — "if the repaired instrument cannot meet them, that is a finding about
the benchmark design" — A1–A6 **cannot be recalibrated on the current answer space.** No choice of X
or Y rescues an empty band. The pre-commitment did precisely what it was written to do: it produced a
stop instead of a fitted threshold.

### What this result does and does not say

- **It does say:** the two-action benchmark design cannot support the preregistered estimand. That is
  a genuine methodological finding, and the project's first real result.
- **It does not say** anything about whether ELL works. It is a statement about the instrument, not
  the hypothesis. H1–H7 remain untested — not unsupported, untested.

### The design constraint this yields

Any v0.8 answer/task space must satisfy:

```
ceiling - null_p95 > primary_effect + X(power)
```

Two independent levers, and both are needed:

1. **Lower the null floor — larger `k`.** With two real actions an always-answering null floors at
   the action marginal (≈0.50). Corridor at the current ceiling by action count:

   | k real actions | null floor ≈ 1/k | corridor at ceiling 0.5714 |
   |---:|---:|---:|
   | 2 | 0.500 | 0.071 |
   | 3 | 0.333 | 0.238 |
   | 5 | 0.200 | 0.371 |
   | 10 | 0.100 | 0.471 |

2. **Raise the achievable ceiling.** `oracle-retrieval` handed the *exact gold evidence* scores only
   0.5714 — the answer stage discards ~43% of perfect evidence. This is the deeper defect: with
   ideal retrieval the ceiling should approach 1.0. A larger `k` alone would widen the corridor while
   leaving the instrument unable to convert good evidence into correct decisions.

Fixing the ceiling is the more important of the two, and it is the same answer-stage problem that has
recurred throughout: the text-only ruling, the namespace leak, A9b's weak power, and now this.

### Consequences

- A1–A6: **stopped**, not superseded-and-pending. No recalibration until v0.8 redesigns the answer
  and task space.
- A7 (chronology), A8 (determinism), A9/A9b (leak battery): **remain in force and remain useful.**
  The infrastructure is sound; the task design is not.
- Phase 3 and beyond: unchanged — still blocked, and now for a better-understood reason.
- Commitment `de1d0be9…`: no band was derived, so it was never used. Release it labelled as
  invalidated historical evidence; the hash proves it was untouched.

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

### Ruling A — re-express as distances, and *derive* the bounds rather than choose them

A1–A6 failed because raw accuracy bands are **floor-dependent**. Replacing one set of magic numbers
with another leaves the same defect. Criteria are restated as **distances** from the two measurable
reference points, per Reviewer:

```
lower bound: observed >= permuted-null 95th percentile + X
upper bound: observed <= oracle-retrieval - Y
```

Distances, not a normalised ratio — the ratio form `(observed - chance)/(ceiling - chance)` is
unstable exactly where we already have trouble, since `ceiling - chance` approaches zero on a
saturated stratum (near sat at 0.5714 for both retrieval and its own oracle).

**X and Y are derived, not chosen:**

- **X** = the minimum difference from the permuted-null 95th percentile that is statistically
  distinguishable at the far-task N, α = 0.05, and the target power — a power calculation, using the
  existing `ell.statistics` cluster machinery.
- **Y** = enough headroom below `oracle-retrieval` to express the preregistered primary effect
  (currently 5 percentage points, pending v0.8) plus its interval half-width, without hitting the
  ceiling — arithmetic.

The band then follows from floor, ceiling, N and α. All four are properties of the design; **none is
an eligible-comparator measurement.** Anyone can recompute it and verify that no eligible number
could have influenced it.

### Contamination — disclosed, not claimed away

Every technical participant has measured eligible conditions: Forge (an unpublished combined
eligible table, voluntarily disclosed), Reviewer (repeatedly, across three branch states), and me
(I reproduced the suite including `direct-insight` at 0.285). **Nobody on this project is blind, and
claiming otherwise would be worse than admitting it.**

So the protection is the removal of discretion above, not asserted blindness. Three further
safeguards:

1. **Forge commits the unpublished eligible table now** — hash published immediately, contents
   revealed at step 5. Same mechanism the project already uses for the sealed seed. It converts a
   disclosure into a verifiable one and protects Forge by proving the figures were not altered after
   the bands were fixed.
2. **Scholar ratifies the procedure**, being the one participant who has not run the instrument. Not
   to author X and Y — a band nobody can verify is no better — but to confirm the derivation
   references only floor, ceiling, N and α, and no eligible measurement.
3. The derivation is written down before use, so an external reader can audit it independently.

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
| A10 | **Answer-stage order invariance** — shuffle a fixed selected evidence set, every condition | emitted action identical |
| A11 | **Structural seed sensitivity** — key statistics across >=8 seeds | between-seed sd `>= 0.5 x` the binomial SE at that stratum's N |

## The seed varies surface text, not structure (2026-08-11)

Found by Reviewer while checking Scholar's uncertainty model. **This is the most consequential finding
in the instrument review, and it is not a leak — nothing in A9 catches it.**

`oracle-retrieval` far accuracy on development, measured across seeds:

| seeds tested | value | sd |
|---|---|---|
| 1729, 11, 42, 101, 777 (Darwin) | `192/336` = **4/7** every time | **0.0000** |
| 8 seeds, source order (Reviewer) | 4/7 | 0.0000 |
| 8 seeds, recency order (Reviewer) | 6/7 | 0.0000 |

Cause, confirmed in `benchmark.py`:

```
481:  is_exception     = index % 11 == 10
482:  is_contradiction = not is_exception and index % 7 == 6
532:  stratum          = ("near", "intermediate", "far")[task_index % 3]
```

The oracle's score is fixed by the template's **modular cadence**. The seed permutes surface text and
never touches structure.

### Consequences, which outrank the band question

1. **`oracle-retrieval` is a constant, not a sample statistic.** So neither a confidence interval nor
   `0.0024 ≈ 0.09 SE` is the right frame for it. Scholar's sampling-robust instinct was the right
   move — and it is what led Reviewer to check across seeds — but the uncertainty model does not apply
   to a quantity with zero variance.
2. **Same-seed reproduction verifies determinism, which was never in doubt.** Phase 1's
   "two independent clean-machine reproductions" exit criterion was always going to be satisfied
   trivially. It is **not** evidence of generalisation, and I had accepted it as though it were.
3. **Development and sealed are structurally the same dataset at different scale.** The seal protects
   surface text, not structure. Anything tuned against development *structure* is tuned against sealed
   structure, and **no sealed-run discipline detects it.** This is a deeper problem than any of the
   four leaks: the seal is the project's core protection, and it is substantially weaker than assumed.
4. **Between-rule SD estimated on development understates the truth**, because seeds do not vary
   structure — and that estimate is exactly what v0.8 sizing depends on.
5. **The ceiling question is settled.** `0.5714` is not a `k=3` structural cap; it is what source
   ordering plus rank discounting yields from this cadence. Recency ordering gives `6/7 = 0.8571` from
   the same evidence. Any construct-impossibility argument must be tested against **6/7**, where
   headroom is ~0.27 and X is not squeezed at all.

### Rulings

- **Structure must be sampled, not fixed.** The generator varies cadence periods, stratum assignment
  and contradiction/exception rates per seed. A seed that only permutes surface text is cosmetic.
- **The sealed partition is drawn with structural parameters independent of development**, not the
  same cadence at larger scale. Without this, sealing is theatre.
- **A8 is retained but demoted in meaning:** same-seed byte-identity is a determinism check and is
  explicitly *not* evidence of robustness. Phase 1's reproduction criterion is amended to require
  different-seed runs showing conclusions stable under structural variation.
- **A11 added** so a zero-variance statistic fails loudly instead of looking like precision.

### A11 sharpened before encoding (2026-08-11)

`sd > 0` was too weak, and Forge's own post-repair data demonstrates why. After A10, the far oracle
does vary across eight development seeds — but only over `0.8482–0.8542`:

| quantity | value |
|---|---|
| spread across 8 seeds | 0.0060 |
| implied between-seed sd | ≈ 0.0017 |
| binomial SE at p≈0.851, N=336 | 0.0194 |
| **ratio observed / genuine-resampling** | **0.09x** |

So the seed now moves the statistic by roughly a tenth of what real structural resampling would
produce. Under `sd > 0` that passes; the underlying defect is untouched.

**A11 is therefore:** between-seed sd `>= 0.5 x` the binomial SE at that stratum's N. At N=336 that
is a floor of `0.0097`, which the current 0.0017 **fails**. The criterion now measures whether
structure is genuinely resampled rather than merely perturbed.

Note also that Forge's post-A10 far oracle of `0.8482` is `285/336`, against Reviewer's recency-order
`6/7 = 288/336`. The A10 order-invariance change moved three tasks; the two figures are consistent and
neither is a constant-cadence artifact in the way `4/7` was.

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
  **empirically calibrated leak-free null**. The **method** is pre-committed; the number is not,
  because the answer stage is still changing.

#### A9b permutation estimand — corrected 2026-08-11

I first approved permuting `ExperienceRecord.rule_id`. **That is a no-op for accuracy.** Forge
caught it: `rule_id` is evaluator-only, and nothing in the selection or scoring path reads it —
correctness is `prediction == task.gold_action` (`benchmark.py:617`), and `rule_id` appears only in
construction. Permuting it leaves null-policy accuracy bit-identical.

The two criteria need **different** permutations, so this is an addition rather than a replacement:

| criterion | permutation | why |
|---|---|---|
| A9 (selection precision) | permute `record.rule_id` | precision is *defined* against rule labels, so this is the correct null |
| A9b (accuracy) | permute complete **task gold-action trajectories between latent rules**, at matched task ordinal and stratum, leaving queries, visible records, chronology and policy outputs fixed | breaks the evidence→answer link while preserving task clustering and the action marginal |

A9b's permutation must be cluster-level (whole rules, not individual tasks) to preserve within-rule
correlation, must hold stratum composition fixed, and must run over a pre-committed number of seeded
permutations. Calibrate on the permuted copy only — never against the real generator, which would
bake in whatever leak is live.

Two further requirements:

- **Per-policy bound, not one shared constant.** The permuted-null accuracy depends on a policy's
  abstention rate: a policy that always answers floors near the gold action marginal (≈0.5), one that
  always abstains floors near 0. A single shared 95th percentile would be too lax for abstainers and
  too strict for answerers, both for reasons unrelated to leakage. Each null policy is therefore
  tested against **its own** permuted distribution.
- **Policy outputs are held fixed, and this is asserted in code.** Recompute correctness against
  permuted gold; never re-run selectors on permuted data. If selections move, the test is circular.
  An assertion, not a comment — it is the one mistake that would silently invalidate the battery.

**Known power limitation.** With two real actions plus abstain, the permuted null essentially
estimates the gold action marginal, so the null distribution is tight around chance and A9b has
limited power against a *small* leak. It reliably catches large ones — all four found so far were
enormous (1.0000 precision, 98.6% concentration) — but it would not reliably catch a 3-point edge.
A9b is a backstop against gross leakage, not a proof of its absence.

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

### THE primary v0.8 question: the action space is the root constraint

Promoted to the top of the v0.8 agenda, not left alongside it. The leak repairs are converging; this
is what remains underneath them.

The two-action space has now caused **three** distinct failures:

1. the text-only answer-stage ruling was unimplementable — no lexical bridge from record text to
   action labels (0/840 verbatim, 8.8% any word overlap);
2. the action namespace *was* the rule namespace, giving an exact rule oracle inside the certified
   boundary;
3. A9b has weak power against small leaks, because with two actions plus abstain the permuted null
   is just the action marginal.

With `k = 3`, chance is 1/3 and the benchmark is close to a coin flip with retrieval as the
tiebreaker. That bounds what *any* positive result could mean, independently of every leak fix.

**The opaque A/B namespace is a leak repair, not the destination.** Nobody should treat it as the
final design. The end state needs both properties at once:

- **large `k`**, shared across rules — so chance is low and retrieval quality dominates the metric
  rather than a coin flip, while no `allowed_actions` set fingerprints its rule;
- **a semantic bridge from record text to action** — so the answer stage *infers* rather than looks
  up, which is the only configuration in which the benchmark measures a decision.

Those two together are the design question. Getting one without the other reproduces either the
namespace leak or the lookup problem. This is the same "option 2" deferred earlier as a nicety; it is
now the central item.

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
