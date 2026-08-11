# Recovered trust requirements (from the closed `ell-core` line)

**Status:** requirements of record. **Recovered:** 2026-08-11. **Owner:** Darwin (ELL Lead).

The `ell-core` implementation line of 2026-08-09 is formally closed. Its commits
(`cf43d64`, `9396689`, `e094416`) are not recoverable, its branches were never pushed, and its
planning documents (`PLANS/ELL_EVALUATION_SCORECARD.md`, `PLANS/ELL_MILESTONE_2_TEST_CONTRACT.md`,
`RESEARCH/ELL_SIMULATION_ARCHITECTURE_REVIEW.md`) no longer exist on any disk we can read.

The only surviving artifact is the channel discussion. This document transcribes the
**requirements** from that line so closing it does not silently drop obligations we already know
we have not met. Nothing here is a result; several items are confirmed *unimplemented* in the
current repo and are recorded as open.

Recovered from evaluation-scorecard review (agent: Honey), architecture trust review and
adversarial harness slice (agent: Bumble). Cross-checked against the current repo by Reviewer's
detector audit, 2026-08-11.

## R1 — Definition of "best"

Best = **highest held-out task utility among configurations that pass every hard constraint**.
Privacy, workspace isolation, deletion, provenance, chronology, consent, unsupported
generalisation, evidence quality and temporal adaptation are **gates**, not penalties that a high
average can cancel. No weighted average may let extra utility compensate for a safety failure.

Among eligible runs, task utility comes first. Unsupported guidance is already a gate — it must
not be re-used as a second optimisation target.

## R2 — Selection must refuse rather than degrade

If no configuration passes every gate, selection **stops with `NoEligibleConfiguration`**. It must
never return the least-bad unsafe run. Selection order is frozen: task utility, amortised utility,
p95 latency, then declared complexity.

*Current status:* the repo's `evaluate_confirmatory_study` does refuse to emit a premature
verdict. Reviewer confirmed, however, that governance, adaptation and replication evidence are
**caller-supplied arguments** and `StudyPrerequisites` is six self-declared booleans — so three of
seven gates are currently fed by hand-typed values. **Open.**

## R3 — A mutant must fail for the intended reason

Detecting a mutant means it fails with the **intended stable failure code** plus the affected
receipt/object id and diagnostic evidence — not merely that some metric moved off zero.

Safety failures resolve to `unsafe`. Quality, adaptation and cost failures resolve to `ineligible`.

The harness must **refuse to use a baseline that already fails one of the target gates**, so a
mutant can never appear "detected" because the starting condition was already unsafe.

## R4 — The five adversarial conditions

| condition | stable gate code | status in this repo (2026-08-11) |
|---|---|---|
| future evidence used | `future-evidence` | **absent** |
| foreign workspace read | `cross-workspace-leakage` | enforced in `ELLCore`; in the study an *input field* nothing computes |
| stale decision after change point | `post-change-stale` | **absent as a detector** (`episodes_since_change` populated, unconsumed) |
| deleted evidence still reachable | `deleted-evidence` | cascade real and tested in core; **no benchmark-side detector** |
| hidden/unaccounted retrieval work | `unaccounted-cost` | **absent** |

Each condition writes one explicit machine-readable failure report per condition under
`adversarial/`.

Three of five have no implementation. This is the single largest recovered gap, and it is why
this document had to be written before the line was closed.

### R4a — sixth condition: `positional-leakage` (added 2026-08-11)

Not present in the recovered five. Stream position must carry no information about the latent
rule. Found live at `6724949`: 98.6% of each task's five most recent visible records belonged to
that task's own rule (4968/5037, against a 4.17% chance baseline on development), which made a
recency window a covert rule oracle that never reads text.

Notably the chronology filter did not cause this — it made it *exploitable*, because before the
filter the recent tail was the end of the whole partition rather than the end of this rule's block.
Fixing one leak exposed another, which is the argument for the A9 battery running continuously
rather than per-review.

## R5 — Runner owns the invariants; policies only propose

The runner owns chronology, permissions, budgets, canonical commits and receipts. Plugins and
policies propose only through **workspace- and time-scoped capabilities**.

*Current status:* violated. There is no chronology comparison anywhere in the selection path;
`run_baseline` hands every selector the entire partition. **Open — highest priority.**

## R6 — Gold labels physically separate from policy-visible objects

Gold labels belong in a separate evaluation artifact with a loader boundary, never in
policy-visible objects. Sealed policy inputs and gold labels require separate, hash-verified
artifacts before confirmatory use.

*Current status:* no eligible selector reads a gold field today (Reviewer verified line by line),
so this is an **exposure, not an active leak** — the fields remain reachable on `TaskCase` and the
boundary is not structural. **Open.**

## R7 — Identical starting conditions per condition

Every condition starts from the **same immutable snapshot** with fresh caches and indexes.

## R8 — Pin more than the seed

Pin canonical serialisation, the RNG algorithm, and generator/code/dependency digests — not only
the seed. The sealed lock must **persist the full study manifest** and survive runner restart, not
merely hold a config hash in memory. It grants **one sealed run only**.

## R9 — Deletion is a closure property

Deletion must be tested as a closure across sources, concepts, summaries, embeddings, caches,
indexes **and content-bearing receipts** — not only canonical rows.

## R10 — The statistical unit is the correlated group

Where events are correlated, the independent stream/persona — in the current design, the **latent
rule** — is the unit of analysis, not the individual query. Individual queries inside one history
are correlated and must not be treated as independent.

*Current status:* v0.7 adopts this correctly. `study.py` still uses a task-level percentile
bootstrap. **Open.**

## R11 — Development/sealed separation

Development sweeps may tune thresholds, retrieval budgets, reflection frequency, consolidation
triggers, confidence rules and policy combinations. The sealed test tunes **nothing**: one frozen
configuration, fixed hashes, seeds, budgets and metrics, one recorded run, failures retained.

## Disposition

R5, R6, R10 and three of the five R4 detectors are open and now tracked here rather than only in
chat. R2's governance-gate content is declared rather than verified and is also open.
These feed the v0.8 contract and the instrument repair.
