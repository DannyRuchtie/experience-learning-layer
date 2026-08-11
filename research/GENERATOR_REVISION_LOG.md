# Generator revision log

**Status:** active. **Started:** 2026-08-11.

This log records every benchmark leak repair, the measurements it invalidated, and who found it.
Entries are append-only. A repaired instrument does not retroactively validate earlier numbers.

| revision | leak | finder | repair | measurements invalidated |
|---|---|---|---|---|
| G1 | Gold `scope` shortcut: rule identity was policy-visible and historical `direct-insight` matched on it. | v0.7 review; independently confirmed by Forge and Reviewer | Remove scope/rule/gold fields from eligible inputs; add projection types. | Historical `direct-insight = 1.0` positive-control claim and all pre-boundary comparator scores. |
| G2 | Future peek: selectors received the whole partition, including later records and outcomes. | Forge; independently confirmed by Reviewer and Darwin | Runner-owned sequence/time/workspace/permission/deletion projection in PR #5. | Every baseline score produced before PR #5 (`f041739`). |
| G3 | Positional leakage: rule-block layout put the task's own rule in 98.6% of its recent five-record tail. | Reviewer; independently reproduced by Darwin and Forge | Seeded shuffled round-robin scheduling, preserving within-rule chronology, in PR #7. | First chronology-safe A1–A8 table at `af52758` and the initial answer-stage table at `6724949`. |
| G4 | Action namespace: `allowed_actions × observed_action` was an exact rule join (same-rule precision 1.0). | Reviewer; independently reproduced by Darwin and Forge | Seed-committed balanced random mapping onto shared opaque actions; add action-filter to A9 in PR #7. | All measurements made before the shared-action repair, including the committed pre-band table hash `de1d0be9c9b36437cab185f8474e853d4c68161d915909ab5b2b906f5200c7a3`. |

## Consequence for claims

The opaque shared action vocabulary bounds the current deterministic instrument to governed
evidence-selection quality. It does not establish semantic action inference or decision quality.
The v0.8 answer-stage design must resolve that construct gap before any broader claim is allowed.
