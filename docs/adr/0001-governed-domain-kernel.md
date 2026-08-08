# ADR 0001: Add a governed provider-neutral memory kernel

- Status: Accepted
- Date: 2026-08-08

## Context

The existing implementation stores conversations, extracted evidence, reflections,
and concepts, but it has no single path that validates model proposals, applies
deterministic policy, commits canonical memories, and excludes superseded or
forgotten records from retrieval. Allowing each pipeline or provider adapter to
make those decisions would make provenance and correction behavior inconsistent.

## Decision

Introduce `ell.domain` as a pure Python domain boundary. Pydantic models define
immutable source, citation, candidate, memory, audit, and retrieval contracts.
`LearningKernel` is the sole application service that advances a candidate through
validation and policy before commit. Its ports have in-memory reference adapters;
database and provider adapters can follow without entering the domain core. The
repository intentionally does not retain the disconnected legacy application and
database scaffold; those are future adapters, not Phase 0 dependencies.

The initial policy is deliberately conservative:

- unsupported non-explicit candidates are rejected;
- sensitive model inference is rejected;
- explicit or user-confirmed candidates may auto-commit;
- other supported inferences wait for review;
- corrections create new memories and superseding revisions instead of edits;
- normal retrieval returns only active, authorized records.

## Consequences

Phase 0 lifecycle and retrieval behavior can run without a database, model, network,
or wall-clock dependency beyond generated timestamps. New storage adapters must
preserve append-only revisions, idempotency, and optimistic concurrency. No
projection or future adapter is canonical implicitly.
