# Phase 2 status

Status: in-memory deterministic reference slice implemented; exit not yet claimed.

Implemented invariants:

- exact source hashes and stable source spans;
- deterministic source, episode, evidence-link, run, and audit identifiers;
- derived episodes, reflections, concepts, applications, and outcomes resolve to
  canonical same-workspace evidence;
- model-shaped reflections enter quarantine and cannot authorize a concept before review;
- immutable concept versions preserve immediate-parent lineage and close prior valid time;
- purpose grants and consent are checked before evidence enters a learning packet;
- conflicting idempotent retries fail rather than producing duplicate mutations;
- applications record the exact concept versions and evidence used;
- outcomes require a separately captured source and never mutate concepts directly;
- source deletion removes content, rejects dependent reflections, deletes dependent
  concept versions, and returns invalidated projection identifiers;
- audit events retain content-minimised structural evidence of governed operations.

Remaining exit evidence:

- add generated/property tests across longer arbitrary lifecycle sequences;
- broaden adversarial tests for mixed sensitivity, concurrent revisions, partial evidence
  deletion, stale reads, malformed lineage, and replay ordering;
- publish an invariant coverage matrix resolving every derived schema field to its
  permitted source or deterministic operation;
- obtain an independent Phase 2 exit run against the tagged Phase 0 schemas.

Persistent databases, approximate retrieval, external memory, provider egress, and crash
recovery are deliberately excluded until Phase 5.
