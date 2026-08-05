# Experience Learning Layer

## Goal

Build a local-first system that converts AI conversation history into
evidence-backed reflections and evolving concepts.

## Core principles

1. Every generated claim must link to original evidence.
2. LLM output is never accepted without schema validation.
3. LLMs interpret meaning; deterministic code controls lifecycle operations.
4. Never overwrite concepts. Create a new version.
5. Separate facts, preferences, goals, beliefs, decisions and behavioural patterns.
6. Preserve timestamps and conversation provenance.
7. Avoid inferring sensitive personal attributes.
8. Prefer simple implementations until evidence shows more complexity is needed.
9. Every feature requires unit tests.
10. Every pipeline must be rerunnable and idempotent.

## Development rules

- Use Python type hints throughout.
- Use Pydantic for all boundaries and model responses.
- Use SQLAlchemy for persistence.
- Use Alembic for schema migrations.
- Use pytest.
- Do not silently catch exceptions.
- Do not make unrelated edits.
- Run formatting, type checking and tests before finishing.
- Explain important design choices in short architecture decision records.

## Commands

- make install
- make db-up
- make migrate
- make test
- make lint
- make typecheck
- make run
