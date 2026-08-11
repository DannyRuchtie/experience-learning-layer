# Invalidated floor/ceiling diagnostic

**Status:** withdrawn; retained as a revision record. **Date:** 2026-08-11.
**Instrument state:** PR #7 `6d11f0c` plus PR #6 `4678982`.
**Open partition:** development seed 1729; sealed commitment only.
**Null calibration:** 1,000 cluster permutations, seed 90009, policy outputs fixed.

The verification suite executed eligible policies but did not print or expose their scores. No
post-repair eligible score was inspected or reported. The previously observed eligible table
remains unopened behind SHA-256 commitment
`de1d0be9c9b36437cab185f8474e853d4c68161d915909ab5b2b906f5200c7a3`.

## Far-stratum floor

| null policy | observed | permuted p95 | exceeds | fixed-output hash |
|---|---:|---:|---|---|
| action-filter | 0.5000 | 0.5000 | no | `sha256:c5272af4dbfd36eea09c65b01e3f2dd3f51023fa4a1115401c6cf36b39c62351` |
| oldest-context | 0.5000 | 0.5000 | no | `sha256:c5272af4dbfd36eea09c65b01e3f2dd3f51023fa4a1115401c6cf36b39c62351` |
| record-id-order | 0.5000 | 0.5000 | no | `sha256:c5272af4dbfd36eea09c65b01e3f2dd3f51023fa4a1115401c6cf36b39c62351` |
| rolling-summary | 0.5060 | 0.5060 | no | `sha256:9dec7611a333119e1e1af6eac205867a222837d7f496d6e96894c18f560b56ef` |
| uniform-random-visible | 0.4970 | **0.5238** | no | `sha256:955f9c2e7046e220e2e4cb346b2b8243e367798d3d1f9a93a84e5e0ed8cb62a7` |

The floor used for band feasibility is the maximum per-policy p95: `0.5238095`.

## Invalid ceiling and withdrawn conclusion

The first diagnostic observed `oracle-retrieval = 0.5714286` on far, intermediate, and near and
incorrectly treated it as a valid ceiling. `_oracle_select` emitted current evidence and stale
counterevidence in generator source order while `_predict` applied a rank discount. Source order
is not an evidence ranking, so this value did not measure the best performance attainable from
perfect evidence.

The resulting comparison was:

```text
0.5714286 - 0.5238095 = 0.0476191
```

Because the ceiling input was defective, the Phase 1 stop conclusion is withdrawn. The arithmetic
procedure used only non-eligible inputs, but a clean procedure cannot rescue an invalid input.

## Required correction

The oracle ordering rule must be fixed on a principle chosen before remeasurement. The proposed
rule is descending `sequence`: it is policy-visible, represents recency, and does not depend on the
resulting score. That rule was encoded before remeasurement. On the combined PR #6 + PR #7
state, without inspecting eligible scores, the repaired `oracle-retrieval` result was:

| stratum | accuracy | tasks |
|---|---:|---:|
| far | 0.857143 | 336 |
| intermediate | 0.857143 | 336 |
| near | 0.830357 | 336 |
| overall | 0.848214 | 1,008 |

The far headroom above the maximum null p95 is therefore `0.857143 - 0.523810 = 0.333333`;
after reserving the preregistered 0.05 effect, 0.283333 remains before the statistically derived
null-separation distance. The former empty-band result does not survive the corrected ceiling.

The observed order sensitivity is itself a construct-validity threat. A rank-discounted answer
stage can produce materially different predictions from identical evidence solely because of
presentation order. That decision rule therefore requires explicit treatment in v0.8 before a
confirmatory comparison.

## Order-invariant answer-stage follow-up

A10 removes list position from `_predict`. For a fixed evidence set, each record is weighted by
its policy score and explicit sequence age relative to the task; permuting selections cannot alter
the emitted action. On that combined state the oracle becomes 0.848214 far, 0.842262 intermediate,
0.830357 near, and 0.840278 overall. Thus the repaired ceiling remains far above the withdrawn
0.571429 value after eliminating ordering as an input.

Before structural sampling, the far oracle across eight open development generator seeds ranged
only from 0.848214 to 0.854167. It was no longer exactly constant, but the narrow range confirmed
that surface-text seed variation contributed little to this structural ceiling.

## Structural-sampling follow-up

The generator now samples change points, contradiction/exception events, and aligned stratum order
from each partition seed. Opposite action mappings share paired profiles, preserving exact
record-weighted A/B balance while allowing between-rule structural variation. Across the same
eight open development seeds, the A10 far oracle ranges from 0.758929 to 0.901786 with population
SD 0.048857. The former near-zero seed variance is therefore removed.

Synthetic sealed-protocol fixtures confirm that different committed sealed seeds produce different
structural summaries while development remains byte-identical. This checks seed isolation and
commitment wiring only; the actual committed sealed seed and sealed outcomes were not opened.
