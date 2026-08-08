# Experience Learning Layer

## Goal

Maintain the living Experience Learning Layer research paper and its small,
provider-neutral Phase 0 kernel. The repository is intentionally paper-first:
the manuscript, schemas, golden corpus, deterministic policy/lifecycle proof,
and reproducible PDF build are the current product boundary.

## Core principles

1. Every generated claim must link to original evidence.
2. Model output is never accepted without schema validation.
3. Models interpret meaning; deterministic code controls lifecycle operations.
4. Never overwrite concepts. Create a new version.
5. Separate facts, preferences, goals, beliefs, decisions and behavioural patterns.
6. Preserve timestamps and conversation provenance.
7. Avoid inferring sensitive personal attributes.
8. Prefer simple research implementations until evidence shows more complexity is needed.
9. Every feature requires unit tests and a paper/status update when it changes a claim.
10. Every pipeline must be rerunnable and idempotent.

## Development rules

- Use Python type hints throughout.
- Use Pydantic for all boundaries and model responses.
- Use pytest.
- Do not silently catch exceptions.
- Do not make unrelated edits.
- Run formatting, type checking and tests before finishing.
- Explain important design choices in short architecture decision records.

Persistence adapters, connectors, model SDKs, and application clients are later
phases. Do not add them to Phase 0 just because the paper describes future ports.

## Commands

- `make install` - install the small paper and Phase 0 development environment
- `make paper` - render the living manuscript to `output/pdf/`
- `make test` - run the Phase 0 contract and kernel tests
- `make lint` - lint source, paper builder, and tests
- `make typecheck` - type-check the domain and evaluation source
- `make clean` - remove local Python/test caches

There is intentionally no database, web server, Docker, provider SDK, or migration
command in this repository yet. Those are later research phases and must not define
the paper's Phase 0 kernel.
