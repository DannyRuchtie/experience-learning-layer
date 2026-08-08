# ADR 0002: Retrieval is a policy-bound service

- Status: Accepted
- Date: 2026-08-08

## Context

Direct database or vector-index access cannot reliably enforce workspace, lifecycle,
scope, sensitivity, contradiction, and evidence rules. A vector projection must also
never become the only copy of canonical information.

## Decision

Consumers issue a typed `RetrievalRequest` and receive an `EvidencePacket`.
The Phase 0 implementation uses deterministic lexical matching and scoring. It
filters before ranking, explains each selection, applies a context budget, includes
known active contradictions, and writes a content-minimized access event. Evidence
can be withheld without removing the stable memory identity.

Future full-text, vector, graph, and learned reranking adapters may contribute
candidates behind this contract, but they cannot bypass authorization or lifecycle
filtering.

## Consequences

The baseline works offline and is deterministic. Its relevance quality is modest by
design; hybrid retrieval can be added as disposable projections while preserving the
same permission and evidence-packet semantics.
