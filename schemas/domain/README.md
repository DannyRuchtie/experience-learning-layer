# Domain schema registry

Canonical Phase 0 JSON Schemas are generated from the immutable Pydantic boundary
by `ell.domain.schema_registry.schema_catalog()`. Every schema has a stable v1 ID;
contract tests ensure an unsupported version cannot silently resolve to v1.

Generated schemas are projections. The Pydantic models and explicit schema version
remain the maintained source so checked-in JSON cannot drift from runtime
validation. A release/export command may materialize the catalog in this directory
when consumers require static files.
