# Answer-stage outcome-gate diagnostic

**Status:** development-only diagnostic. **Date:** 2026-08-11.  
**Base:** `f041739c5caca1712c79b78fc31917c29a1b16a1` (merged policy-boundary PR #5).  
**Environment:** Python 3.14.6, Darwin arm64.  
**Open-data seed:** `1729`; sealed data was not generated or opened.

## Change measured

The shared deterministic answer stage previously discarded every selected episode whose outcome
was not observed by the task time. Only 6.1% of visible gold evidence had an observed outcome, so
the gate imposed an artificial `0.2857` ceiling on oracle retrieval.

The repaired rule keeps the recorded action visible, gives an observed outcome full evidential
weight, gives a pending outcome half weight, and rejects actions outside the task's declared
allowed set. `oracle-concept` no longer returns `gold_action` directly; it uses the same answer
stage as every other condition. The half-weight was selected as the minimal symmetric quality
discount before the results below were measured; it was not tuned against A1–A8.

## Development results

| condition | far | intermediate | near | overall |
|---|---:|---:|---:|---:|
| no-memory | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| maximum-context | 0.5714 | 0.5714 | 0.5714 | 0.5714 |
| bm25 | 0.1994 | 0.5446 | 0.5714 | 0.4385 |
| exact-vector | 0.1012 | 0.5208 | 0.5714 | 0.3978 |
| fused-retrieval | 0.1935 | 0.5536 | 0.5714 | 0.4395 |
| rolling-summary | 0.7857 | 0.8571 | 0.7143 | 0.7857 |
| direct-insight | 0.0506 | 0.3095 | 0.3988 | 0.2530 |
| oracle-retrieval | 0.5714 | 0.5714 | 0.5714 | 0.5714 |
| oracle-concept | 1.0000 | 0.9286 | 0.9286 | 0.9524 |

## A1–A8 readout

| criterion | result | evidence |
|---|---|---|
| A1 eligible comparator in `[0.25, 0.45]` on far | **fail** | Eligible far scores are 0.0506, 0.1012, 0.1935, 0.1994, and 0.7857. |
| A2 every eligible pair separated by `>= 0.02` on far | **fail** | BM25 and fused retrieval differ by 0.0060. |
| A3 maximum-context exceeds no-memory by `>= 0.05` on far | **pass** | Difference is 0.5714. |
| A4 known-good non-oracle control reaches `>= 0.60` on far | **not available** | The v0.8 control is not implemented yet. |
| A5 strict ordering on every stratum | **fail** | Rolling summary exceeds oracle retrieval on all three strata. |
| A6 oracle-retrieval headroom over best eligible near is `>= 0.10` | **fail** | Headroom is -0.1429 because rolling summary scores 0.7143. |
| A7 chronology violations | **pass locally** | Projection regression tests enforce sequence, time, workspace, permission, deletion, and outcome availability. |
| A8 deterministic reruns | **pass locally** | Dataset and baseline result hashes are asserted equal across repeated same-seed runs. |

## Unexpected result

Removing the outcome gate reveals that `rolling-summary` is stronger than the nominal
`oracle-retrieval` ceiling. This is not evidence that rolling summary is super-oracular. The
oracle emits current gold evidence and stale counterevidence in source order with equal scores;
the rank-aware answer stage therefore overweights older evidence. Rolling summary instead selects
the latest five records, which tracks the interleaved regime change. The oracle's ordering and
retrieval-budget contract must be specified before it can serve as an information ceiling. The
acceptance thresholds were not changed in response.

## Verification

`make verify` completed after the change: schema export 36, Ruff clean, strict mypy clean across
12 source files, and 37 tests passed in 153.53 seconds.
