# Phase 0 exit report

Status: implementation-complete candidate; immutable release still required.

The v0.6 research contract fixes the primary paired estimand, eligible baseline set,
development-only selection rule, quantitative gates, cost boundary, power assumptions,
exclusions, sealed-seed policy, and the distinction between a provisional Phase 4 verdict
and the final external-replication gate.

Machine-readable Draft 2020-12 JSON Schemas in `schemas/v0.6/` are generated directly
from the strict runtime contracts. Their manifest records a canonical digest for every
schema. The publication and implementation therefore share names and fields rather than
maintaining a second handwritten schema interpretation.

The synthetic worked cases cover support, counterevidence, revision, deletion,
permission revocation, derived-state invalidation, and unsafe cross-workspace retrieval.

Local exit evidence required before tagging:

- `python3 -m ell.schema_export` reproduces every committed schema and manifest;
- `pytest` passes contract, adversarial, lifecycle, and deterministic benchmark tests;
- `ruff check` and `mypy` pass;
- `quarto render` produces the HTML reading edition and PDF from canonical sources.

Publication exit requires an immutable `v0.6` tag or release pointing at the verified
commit. Until that external publication action occurs, Phase 0 is not formally frozen.
