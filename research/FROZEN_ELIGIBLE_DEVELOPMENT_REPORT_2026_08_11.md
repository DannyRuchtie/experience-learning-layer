# Frozen eligible-comparator development measurement

**Source state:** `main` at `3da8b23eba3e42894da7ec3486b416c77da22317`.
**Partition:** development only, across open structural seeds 1729, 11, 42, 101, 777, 2026,
31337, and 8080. The sealed partition was not generated.
**Pass rule:** accuracy must be strictly greater than the already-fixed q99.9 mark for the same
seed and stratum.

## Primary result

No current eligible comparator clears the primary far-stratum mark robustly across seeds.

| comparator | far mean | between-seed SD | far seed passes |
|---|---:|---:|---:|
| bm25 | 0.477679 | 0.025034 | 0 / 8 |
| direct-insight | 0.501488 | 0.057653 | 1 / 8 |
| exact-vector | 0.492560 | 0.057422 | 1 / 8 |
| fused-retrieval | 0.484375 | 0.047938 | 1 / 8 |

The three passes all occur on seed 31337. Their far scores are 0.633929 (direct-insight),
0.604167 (exact-vector), and 0.589286 (fused-retrieval), against that seed's 0.571429 mark.
On every other seed all four comparators fail. This is seed-specific performance, not a stable
intermediate comparator.

The instrument retains a non-empty null-to-oracle corridor, but the current comparator set does
not occupy it reliably. Therefore a strongest eligible baseline cannot yet be selected for the
confirmatory estimand.

## Sizing consequence

The artifact reports descriptive far-rule accuracy SDs for each comparator, but they are not the
quantity required by `clusters_for_power`. The contract requires the between-rule SD of the paired
ELL-minus-comparator difference. That quantity cannot be estimated until both a defensible
comparator and a development ELL condition exist. Substituting comparator-only variation would
silently change the estimand.

The already-approved self-managed flat-file baseline is cited in the paper but is absent from both
the executable comparator set and v0.8. It is the remaining prespecified Phase 1 candidate. It
should be implemented and measured on development without moving the frozen pass marks. If it also
fails to clear the far mark robustly, Phase 1 reaches its stop/revise condition and the task or
answer construction must change before model-assisted ELL work or a sealed run.

## Reproducibility

Canonical artifact: `research/FROZEN_ELIGIBLE_DEVELOPMENT_2026_08_11.json`.
Artifact SHA-256: `01c2999c76f85d820308fed53ff81c8b40602d4e4f494c62e42cd9827b1efe2d`.

The artifact records every seed/comparator/stratum score, matching q99.9 mark, margin, and pass
decision. Eligible outputs were first observed only after the pass marks were fixed on `main`.
