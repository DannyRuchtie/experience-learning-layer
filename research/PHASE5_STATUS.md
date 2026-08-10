# Phase 5 status

Status: conformance tooling implemented early; phase is not yet eligible under the contract.

Implemented deterministic checks:

- in-memory and SQLite canonical substrates share identity, canonical hashing,
  idempotency, collision rejection, workspace isolation, ordered listing, and tombstones;
- lexical and exact character-trigram projections rebuild deterministically, preserve
  workspace isolation, and invalidate every document derived from a deleted source;
- TurboVec and TencentDB Agent Memory are represented as unavailable optional adapters;
- optional adapters are candidate/retrieval-only and cannot perform canonical writes.

Local conformance currently passes for in-memory, SQLite, lexical, and exact-vector
conditions. These are software results, not comparative performance claims.

Remaining:

- a qualifying positive Phase 4 verdict before formally entering Phase 5;
- HNSW and a frozen TurboVec adapter/version;
- licensed frozen fixtures for external-memory adapters;
- latency, storage, rebuild, crash-recovery, and deletion measurements under matched data;
- provider-egress enforcement tests for every external adapter.

