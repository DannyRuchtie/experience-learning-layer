# Positional-leak repair diagnostic

**Status:** development repair; no sealed outcomes inspected. **Date:** 2026-08-11.
**Base:** `f041739c5caca1712c79b78fc31917c29a1b16a1` (merged policy boundary).
**Environment:** Python 3.14.6, Darwin arm64.
**Seeds:** open `1729`; sealed generation seed `481516` used only for structural null testing.

## Failure

The generator emitted every record and task for one latent rule before beginning the next rule.
Across development tasks, 4,968 of 5,037 records in the most recent five-record visible tail
(98.6%) belonged to the task's own latent rule, versus 4.17% chance for 24 rules. A policy could
therefore recover latent-rule identity from stream position without reading record text.
`rolling-summary` exploited this and was suspended from the eligible comparator set.

## Repair

Each rule's internal record/task order is preserved. The partition scheduler then emits one event
per active rule per round and deterministically shuffles rule order every round. Sequence and
observation timestamps are reassigned after scheduling; each outcome keeps its original delay
relative to its record observation time. Rule order is therefore not encoded by a fixed modulo
position, while change points, gold evidence state, and within-rule chronology remain intact.

## Structural null result

The regression computes the latest five runner-visible records for every task and compares their
same-rule rate with the tier-specific chance rate `1 / rule_count`.

| partition | rules | same-rule recent records | total recent records | observed | chance |
|---|---:|---:|---:|---:|---:|
| train | 12 | 100 | 1,200 | 8.33% | 8.33% |
| development | 24 | 210 | 5,040 | 4.17% | 4.17% |
| sealed structure | 54 | 280 | 15,120 | 1.85% | 1.85% |

The test uses a three-standard-error upper bound derived from each partition's own rule count,
not a constant threshold. It covers all three tiers on every full-suite run. No accuracy or
quality metric is computed from sealed tasks.

## Verification

`make verify` completed after the repair: schema export 36, Ruff clean, strict mypy clean across
12 source files, and 38 tests passed in 152.28 seconds. Performance acceptance criteria remain
uninterpretable until this branch and the pending-outcome tie-break branch are combined.
