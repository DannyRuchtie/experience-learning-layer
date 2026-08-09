# Experience Learning Layer

## Goal

Maintain the living Experience Learning Layer research paper, its visual HTML and
PDF editions, and the small provider-neutral kernel that makes the paper's core
contracts executable. The repository is paper-first; it is not an application.

## Core principles

1. Every generated claim must link to original evidence.
2. Model output is never accepted without schema validation.
3. Models interpret meaning; deterministic code controls lifecycle operations.
4. Never overwrite concepts. Create a new version.
5. Separate facts, preferences, goals, beliefs, decisions and behavioural patterns.
6. Preserve timestamps and conversation provenance.
7. Avoid inferring sensitive personal attributes.
8. Prefer simple research implementations until evidence shows more complexity is needed.
9. Every feature requires tests and a paper/status update when it changes a claim.
10. Every pipeline and publication build must be rerunnable and idempotent.

## Repository boundary

Keep only artifacts that help a reader understand, inspect, reproduce, or evaluate
the paper: manuscript sources, diagrams, HTML/PDF builders, schemas, examples,
golden cases, the governed kernel, and its tests. Product applications, client
shells, provider SDKs, hosted services, sync, and database deployments are outside
this repository.

## Development rules

- Use Python type hints throughout.
- Use Pydantic for all boundaries and model responses.
- Use pytest.
- Do not silently catch exceptions.
- Do not make unrelated edits.
- Run formatting, type checking, tests, and publication checks before finishing.
- Keep diagrams consistent across README, HTML, and PDF from shared definitions.
- Explain important design choices in short architecture decision records.

## Commands

- `make install` - install the paper and research-kernel environment
- `make paper` - render PDF, HTML pages, CSS, and SVG diagrams
- `make pdf` - render the living manuscript to `output/pdf/`
- `make html` - render the reading edition to `docs/`
- `make test` - run contract, kernel, and publication tests
- `make lint` - lint source, paper builders, and tests
- `make typecheck` - type-check the domain and evaluation source
- `make check` - run lint, type checking, tests, and publication verification
- `make clean` - remove local Python/test caches

There is intentionally no app, web server, database, Docker, migration, provider,
or deployment command in this repository. The generated `docs/` tree is static and
can be hosted by GitHub Pages without a runtime.
