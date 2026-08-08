# L - Experience Learning Layer architecture

Status: Foundation architecture, verified Phase 0 contract, and Phase 1 capture preview
Architecture style: Local-first, event-driven, ports and adapters, provider-neutral

## Product definition

L is an open, local-first experience-learning layer that turns attributable
evidence into governed, evolving memory and supplies the smallest useful,
explainable context to an authorized person, application, or AI.

The research question is whether a model-independent layer can transform long
histories into evidence-backed, revisable concepts that improve future decisions
without modifying model weights. Retrieval alone is not learning. The core loop is:

```text
sources -> events -> episodes -> candidates -> governed memory
        -> retrieval -> behavior -> outcomes -> revision
```

Source artifacts, interpretations, and durable memories are distinct. Models can
propose typed candidates; deterministic code validates, applies policy, and commits.

## Product principles

1. Learning is the product; chat is one interface.
2. Source, interpretation, and durable memory remain separate.
3. Models propose; deterministic policy commits.
4. Corrections outrank inference and create new versions.
5. Retrieval is scoped and budgeted, not a history dump.
6. Every derived claim retains exact provenance.
7. Canonical records and exports remain provider-neutral.
8. Local-only operation is a supported topology.
9. Users can inspect, correct, scope, pin, archive, and forget.
10. Sensitivity, consent, retention, and sharing policy travel with records.

## Memory layers

- Source memory preserves immutable captured evidence and addressable spans.
- Working memory holds expiring task and conversation state.
- Episodic memory records bounded events, actions, and outcomes.
- Semantic memory stores temporal facts and generalizations.
- Preference memory stores scoped, explicit or carefully inferred choices.
- Procedural memory stores versioned reusable workflows and approval points.
- Prospective memory stores commitments, reminders, and open threads.
- Relational memory stores typed, temporal, evidence-backed connections.
- Reflective memory stores uncertainty, utility, contradictions, and knowledge gaps.
- Policy memory stores system boundaries and is never ordinary model context.

These layers can share infrastructure but do not share identical authority,
lifecycle, or retrieval behavior.

## Canonical contracts

Canonical objects use stable UUIDs, explicit schema versions, ISO-8601 timestamps,
workspace scope, and JSON-compatible values. The Phase 0 schema registry exposes:

- `SourceArtifact` and stable `SourceSpan` evidence anchors;
- `ExperienceEvent` and `Episode` normalization boundaries;
- `CandidateMemory`, quarantined from normal retrieval;
- immutable revisions of `MemoryRecord`;
- append-only, content-minimized `AuditEvent`;
- `RetrievalRequest` and `EvidencePacket`.

The versioned JSON Schema catalog is generated from the Pydantic boundary in
`ell.domain.schema_registry`. IDs have the form:

```text
https://l.local/schemas/domain/{object}.v1.json
```

Breaking changes require a new schema version. Readers may tolerate additive
fields, but a v1 identifier never silently points to a v2 contract.

## Event and episode normalization

Connectors emit immutable source artifacts and normalized events. Provider-specific
records do not enter reflection, concept, policy, or retrieval services. Generic
events include user and assistant messages, tool calls and results, file changes,
decisions, feedback, and external events. Events can be grouped into bounded
episodes containing inputs, responses, actions, observations, and outcomes.

Stable source, event, and episode IDs make ingestion rerunnable. The same connector,
external reference, version, and event identity produce the same IDs. This enables
at-least-once capture and incremental reimport without duplicate experiences.

Historical ChatGPT ingestion should use a documented data export, preserve raw
conversation structure and timestamps, and normalize into these contracts. Live
Codex ingestion may later map thread, turn, message, tool, and result events to the
same boundary. Neither connector may define the domain model.

## Learning pipeline

1. Capture an immutable source under an idempotency key.
2. Normalize it without deleting the original representation.
3. Segment it into stable, citable spans and normalized events or episodes.
4. Classify sensitivity, scope, consent, retention, and untrusted content.
5. Ask specialized processors for small, typed candidates.
6. Resolve entities conservatively and keep ambiguous merges pending.
7. Compare candidates with active memory for duplicates, temporal changes,
   contradictions, scope refinements, and supersession.
8. Apply deterministic policy.
9. Commit an immutable memory revision through the sole commit service.
10. Rebuild disposable search, vector, graph, and timeline projections.
11. Route consolidation output through the same candidate and policy path.
12. Record explicit feedback and observed outcomes as new evidence.

Every stage is idempotent, restartable, and versioned. A failed pipeline remains
pending or failed and resumes from its latest valid checkpoint; it is never reported
as an empty success.

## Candidate policy

Candidate states are:

```text
proposed -> validated -> auto_committed | awaiting_review | rejected | merged
```

The initial conservative policy is:

| Candidate | Default |
|---|---|
| Explicit user statement or correction | Validate, then commit |
| User-confirmed candidate | Commit |
| Ordinary supported model inference | Await review |
| Inferred procedure | Await review |
| Unsupported non-explicit claim | Reject |
| Sensitive model inference | Reject |

A candidate cannot cite a missing span, cross workspace boundaries, lower source
sensitivity, or supersede a stronger-authority memory. The commit service uses
optimistic concurrency and creates a new record while closing the superseded
revision. It never edits a claim in place.

## Retrieval and evidence packets

Retrieval is a service, not database access. Every request includes actor, purpose,
workspace, scope, allowed types, maximum sensitivity, evidence preference, and a
context budget. Processing order is:

1. authorize and filter by workspace and policy;
2. interpret query scope and intent;
3. combine lexical, vector, relation, temporal, and pinned candidates;
4. remove forgotten, expired, superseded, or disallowed records;
5. rerank by relevance, scope, authority, confidence, freshness, and utility;
6. restore the minimum supporting evidence;
7. return a budgeted evidence packet and record a content-minimized trace.

Phase 0 implements deterministic lexical retrieval so it works offline and can be
tested without an index. Later full-text, HNSW, TurboVec, exact-vector, graph, and
learned-reranking adapters may generate candidates but cannot bypass policy filters.
Known material high-authority contradictions are returned together.

## Component boundaries

The domain core contains only schemas, authority rules, lifecycle rules, policy,
reconciliation, retrieval contracts, and domain events. It has no database,
network, vendor SDK, or model dependency.

Application services coordinate capture, processing, review, correction, forgetting,
retrieval, procedure execution, export, and provider management through ports.

Stable ports include artifact and memory repositories, an event ledger, search,
association and relation indexes, structured model and embedding providers,
connectors, secrets, sync, jobs, policy, audit, and clock.

Adapters may use SQLite, PostgreSQL, content-addressed files, FTS5, HNSW, TurboVec,
OpenAI, Anthropic, local runtimes, OS keychains, or encrypted relays. Vendor response
objects and provider IDs do not become canonical domain identity.

## Provider and agent integration

Four concerns remain separate:

- L user identity;
- workspace authorization;
- model-provider credentials;
- connector grants.

OpenAI and Codex support distinct integration directions:

1. L calls an API through the provider-neutral model port.
2. ChatGPT, Codex, or another client calls L through a narrow MCP server.
3. L optionally supervises a documented local Codex runtime.
4. L exports a scoped Markdown/JSON context package for manual handoff.

An API key is not an L login. A consumer ChatGPT subscription is not assumed to be
a third-party application credential. MCP read, evidence, proposal, correction, and
outcome tools receive separate capabilities. Agents normally propose; L commits.

## Local-first persistence and sync

A reference local implementation may use SQLite for canonical metadata and events,
content-addressed encrypted files for large artifacts, and replaceable full-text and
vector projections. Offline operation always supports capture, browsing, correction,
lexical retrieval, installed processors, and queued sync/provider work.

Sync exchanges encrypted, authenticated events and blobs. Tombstones dominate older
writes; model-derived changes cannot override explicit user revisions. A local device
owns a complete usable state. Cloud sync and hosted processing are optional.

## Security and privacy

Imported content is untrusted and cannot become instructions. Required controls
include encryption, minimal connector scopes, short-lived agent tokens, sandboxed
parsers, egress policy before remote calls, restricted-field routing, and auditable
actions without raw content or secrets in logs.

Forgetting immediately excludes a record from retrieval, writes a tombstone, removes
derived projections, triggers evidence-aware invalidation, and propagates deletion
where supported. Sensitive trait inference is disabled for automatic learning.

## Evaluation

Evaluation covers evidence-supported precision, hallucinated candidates, entity
resolution, sensitivity violations, contradiction detection, retrieval quality at a
fixed budget, stale-memory leakage, citation correctness, correction rates, context
tokens, latency, storage, model calls, and downstream behavioral improvement.

The versioned synthetic golden corpus includes paraphrase, duplicate evidence,
explicit correction, contradictions, scope, temporal change, sensitive information,
prompt injection, multilingual evidence, and similar identities. Model, prompt,
ranking, policy, and schema changes run against this corpus.

## Delivery sequence

### Phase 0 - contracts and evaluation

- Version canonical objects and expose JSON Schemas.
- Run the pure domain core without database or model dependencies.
- Supply a deterministic mock structured-output provider.
- Freeze a synthetic golden corpus.
- Encode invariants as unit and contract tests.

Exit: candidates can be validated, governed, committed, corrected, contradicted,
forgotten, and retrieved as a scoped evidence packet entirely in memory.

### Phase 1 - episode and local learning foundation

- Import ChatGPT export ZIPs incrementally with deterministic identity.
- Capture live macOS chat messages before provider calls and close completed turns
  as deterministic episodes through the same canonical contracts.
- Add SQLite and content-addressed artifact adapters.
- Add manual/file capture and a deterministic processing pipeline.
- Export canonical JSONL and Markdown.

The first Phase 1 preview uses append-only JSONL before SQLite so the capture
contract can be exercised without choosing the later memory or retrieval substrate.
TencentDB Agent Memory is a comparison and possible adapter behind these ports, not
the canonical store. Google Vertex AI Memory Bank is a later hosted option subject
to workspace egress policy; local-only capture remains supported.

### Phase 2 - associations, reflection, and useful daily workflows

- Benchmark exact-vector, HNSW, and TurboVec association adapters.
- Add reflection scheduling, contradiction discovery, consolidation, and review.
- Add working/prospective memory and outcome feedback.

### Phase 3 - agent interoperability

- Ship read-only MCP first, then proposal tools and approval UI.
- Add scoped remote authorization and agent access audit.
- Keep managed Codex runtime integration behind a feature flag until documented.

### Phase 4 - encrypted sync and teams

- Add device identity, encrypted event sync, conflict resolution, shared workspaces,
  hosted workers, organizational identity, retention, and administrative controls.

### Phase 5 - ecosystem

- Stabilize extension SDKs, signed packages, permission review, compatibility tests,
  and third-party connectors and adapters.

## Non-negotiable invariants

- No durable memory without exact evidence or explicit user authorship.
- No active memory is both superseded and normally retrievable.
- No source crosses a provider boundary forbidden by its policy.
- No extension receives undeclared capabilities.
- No secret appears in logs, prompts, exports, or canonical records.
- No forgotten record reappears after sync or projection rebuild.
- No model output is executed or committed without validation.
- No material known high-authority contradiction is omitted from retrieval.
- No projection is the only copy of canonical information.
- No provider-specific identifier is the sole domain identity.
- No implicit signal silently becomes a sensitive durable inference.
- No failed pipeline is reported as completed.

## Initial decisions

1. Python is the research and orchestration language; Rust is reserved for measured
   performance bottlenecks.
2. Canonical memory is provider-neutral and evidence-backed.
3. Sources are immutable; revisions and tombstones preserve history.
4. Models cannot write canonical memory directly.
5. Indexes are rebuildable projections; retrieval is hybrid, never vector-only.
6. Local-only operation and open export are core product modes.
7. Research reproducibility and inspectability precede product optimization.
8. ChatGPT export is the first historical source; Codex is a candidate live source
   only after event and episode contracts stabilize.
9. TurboVec and HNSW are replaceable association-index candidates to benchmark, not
   architectural commitments.
10. Evaluation gates model, prompt, policy, ranking, and schema changes.
