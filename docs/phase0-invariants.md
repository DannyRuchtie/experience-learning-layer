# Phase 0 invariant coverage

This matrix distinguishes executable Phase 0 proof from later adapter and sync work.
An invariant is not marked covered merely because architecture prose mentions it.

| Invariant | Phase 0 evidence | Status |
|---|---|---|
| Durable memory requires evidence or explicit authorship | Model validator, policy, kernel tests | Covered |
| Superseded memory is excluded from ordinary retrieval | Immutable revision and retrieval test | Covered |
| Model output is validated before commit | Pydantic mock provider and kernel validation tests | Covered |
| Material known contradiction is returned | Forward/reverse contradiction retrieval test | Covered |
| Provider identity is not domain identity | Stable connector-neutral ID contract test | Covered |
| Sensitive implicit inference is not durable | Policy and test | Covered |
| Forgotten memory is excluded | Tombstone revision and retrieval test | Covered locally |
| Workspace/sensitivity boundaries precede relevance | Candidate and retrieval tests | Covered locally |
| Source egress follows provider policy | Requires provider router and egress adapter | Deferred |
| Extension gets only declared capabilities | Requires extension host | Deferred |
| Secrets never enter logs/prompts/exports | Requires secret and provider adapters | Deferred |
| Forgotten data cannot return after sync/rebuild | Requires persistent projections and sync | Deferred |
| Projection is never the only canonical copy | Requires projection contract suite | Deferred |
| Failed pipeline resumes and never reports empty success | Requires job/checkpoint runtime | Deferred |

Deferred rows are release gates for the phase that introduces the relevant adapter;
they are not waived.
