# Floor and ceiling on the merged tree

**Measured:** 2026-08-11 by Darwin, on `main` @ `e895a31` (all repairs merged).
**Eligible comparators were not run.** Only the permuted-null floor and the oracle ceiling, which
are the two inputs the band derivation is permitted to use.

Development partition, 8 seeds, 1,000 gold-trajectory permutations per seed.

## Results

| stratum | ceiling (mean, sd) | floor (mean, sd) | corridor mean | corridor min |
|---|---|---|---|---|
| near | 0.8426 (0.0341) | 0.5413 (0.0067) | +0.3013 | +0.2440 |
| intermediate | 0.8702 (0.0514) | 0.5432 (0.0089) | +0.3270 | +0.2560 |
| **far** (primary) | **0.8322 (0.0489)** | **0.5387 (0.0052)** | **+0.2935** | **+0.2232** |

Per-seed far corridor: 0.2708, 0.2619, 0.2351, 0.3185, 0.3512, 0.3661, 0.3214, 0.2232.

## What this settles

**The empty band is gone, and not marginally.** The worst seed leaves **+0.2232** of far corridor
against a preregistered primary effect of **0.0500** — roughly 4.5x the effect in headroom. The
earlier "Phase 1 stop" arithmetic (corridor 0.0476 against effect 0.0500) was an artifact of the
source-ordering ceiling, exactly as the retraction concluded.

**A11 passes comfortably.** Far ceiling sd is 0.0489 against an A11 floor of ~0.0102 (0.5x the
binomial SE at N=336). Structure is genuinely resampled.

**A9b is clean.** One breach across 8 seeds x 3 strata x 5 null policies = **1 of 120 tests**:
`uniform-random-visible` at intermediate, observed 0.5714 against null p95 0.5476.

A p95 threshold has a 5% false-positive rate *by construction*, so 120 tests would nominally produce
about 6 breaches under a true null. Observing 1 is **below** the nominal rate and is not evidence of
leakage. (The tests are not independent — same dataset, correlated policies — so 6 is an
approximation, not an exact expectation.)

## Open question for the band derivation — needs ratification

`Y` is straightforward: the primary effect plus its interval half-width, below the ceiling.

**`X` is not yet fully derivable, and this should not be glossed.** X is the minimum distance above
the null p95 that is statistically distinguishable. That requires a variance estimate, and there is a
genuine choice about *which* variance:

- the **null distribution's own spread** across permutations — available now, uses no eligible
  measurement, but answers "could this comparator be a null?" rather than "can we separate two
  comparators?";
- the **SD of the paired difference** between a comparator and the null — the quantity the
  confirmatory test actually uses, but it cannot be estimated without running a comparator, which
  would contaminate the band.

These are not equivalent and they will give different X. Taking the first is defensible and keeps the
derivation blind; it should be an explicit, ratified choice rather than a silent default.

**Scholar to ratify** which variance the derivation uses, on the record, before X is computed —
Scholar is the only participant who has not measured eligible conditions. Recomputation must use
`ell.statistics`, not a closed-form heuristic, per the standing requirement after the last chance-model
error.

## Not done here

Sealed was not generated or measured. Forge's committed eligible table `de1d0be9…` remains unopened.
