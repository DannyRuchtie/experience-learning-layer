# Experience Learning Layer

## Goal

Maintain the living Experience Learning Layer research paper, its provider-neutral
kernel, and the small Phase 1 live-chat episode-capture preview. The repository
remains paper-first: new client or adapter behavior must preserve the canonical
schemas, deterministic lifecycle, golden corpus, and reproducible PDF build.

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

Keep Phase 1 adapters narrow. The macOS chat client and append-only JSONL capture
adapter are in scope. Databases, sync, hosted memory, vector stores, MCP, and further
provider SDKs remain later work unless explicitly promoted with an ADR and tests.

## Commands

- `make install` - install the small paper and Phase 0 development environment
- `make paper` - render the living manuscript to `output/pdf/`
- `make test` - run the Phase 0 contract and kernel tests
- `make lint` - lint source, paper builder, and tests
- `make typecheck` - type-check the domain and evaluation source
- `make clean` - remove local Python/test caches
- `make app-test` - build and test the macOS chat capture client
- `./script/build_and_run.sh --verify` - build, launch, and verify the macOS app

There is intentionally no database, web server, Docker, or migration command in this
repository yet. Remote providers remain replaceable adapters and must not define the
paper's domain kernel.
