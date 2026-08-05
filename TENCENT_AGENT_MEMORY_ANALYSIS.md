# TencentDB Agent Memory — Compatibility Analysis with ELL

**Reference:** `data/raw/ELL_Paper_v0.1.md` (21-page working draft, v0.1)  
**Target:** `https://github.com/TencentCloud/TencentDB-Agent-Memory`  
**Date:** 5 August 2026

## Executive Summary

**Verdict: Partially compatible. Not a drop-in replacement for ELL's memory model, but useful as an L0/L1 ingestion layer.**

TencentDB Agent Memory is a **practical agent-memory runtime** focused on reducing repetitive work across agent sessions. It extracts memories from conversations and provides retrieval. ELL is a **research architecture** focused on the epistemic lifecycle of concepts — evidence-grounded, versioned, auditable, and directly measurable.

They solve different problems with different guarantees:

| Dimension | TencentDB Agent Memory | ELL (this project) |
|-----------|----------------------|-------------------|
| **Primary goal** | Reduce repetitive agent work | Produce verifiable, revisable concepts |
| **Memory model** | L0 (raw) → L1 (extracted) → L2 (scenario) → L3 (profile) | Episode → Association → Reflection → Concept (versioned) |
| **Evidence linking** | `source_message_ids` (one-way) | Bidirectional: concept ↔ evidence ↔ counterevidence |
| **Lifecycle** | Priority-based, no explicit states | proposed → corroborated → contested → revised → superseded → retired |
| **Counterevidence** | Not explicitly modeled | First-class citizen, drives revision |
| **Confidence** | Numeric priority (0-100) | Computed from observable signals (evidence quality, diversity, contradiction, outcome) |
| **Temporal validity** | `activity_start_time` / `activity_end_time` (episodic only) | `valid_from` / `valid_until` on every concept version |
| **Revision** | Version increment on update/merge | Immutable versions with full lineage (revises, supersedes, merges, splits) |
| **Deletion** | JSONL cleanup by memory-cleaner | Cascade deletion with audit trail (privacy + scientific requirement) |
| **Evaluation** | PersonaMem benchmark (+59%) | Preregistered: concept correctness, evidence precision/recall, calibration, transfer, cost |
| **License** | MIT | MIT (same) |
| **Language** | TypeScript (Node.js ≥ 22) | Python 3.9+ (FastAPI, SQLAlchemy) |
| **Storage** | SQLite + local JSONL files | PostgreSQL + pgvector (planned: SQLite baseline) |
| **Model coupling** | Requires LLM API for extraction | Model-agnostic interface (LM Studio, OpenAI, fake) |

## Where They Align

### L0 Raw Episode Storage
Both preserve raw conversations in an append-only store:
- TencentDB: `conversations/YYYY-MM-DD.jsonl` (one message per line)
- ELL: `Conversation` table with `raw_data` JSON column

### L1 Atomic Memories ↔ Evidence
Both extract structured memories from raw conversations:
- TencentDB: `MemoryRecord` with `type`, `priority`, `scene_name`, `source_message_ids`
- ELL: `Evidence` with `type`, `statement`, `subject`, `temporal_scope`, `importance`, `extraction_confidence`

### Retrieval
Both support keyword (BM25) + vector retrieval:
- TencentDB: BM25 + embedding + hybrid, capped by item count and character budget
- ELL: Hybrid scoring (semantic + subject + entity + type + temporal)

### Scene/Scenario Grouping
Both group related memories:
- TencentDB: `scene_name` field on L1 memories, L2 "scenario" level
- ELL: Evidence clustering by subject, temporal scope, and evidence type compatibility

### Team/User/Agent Isolation
Both support multi-tenant access control:
- TencentDB: `teamId`, `userId`, `agentId` on every record
- ELL: Planned `AccessControl` and `SubjectNamespace` (not yet implemented)

## Where They Diverge (Critical Gaps for ELL)

### 1. No Concept Lifecycle State Machine
TencentDB has no concept states (proposed, corroborated, contested, revised, superseded, retired, deleted). Memories are just records with a numeric priority. ELL's entire research hypothesis depends on this lifecycle.

### 2. No Counterevidence Model
TencentDB's `DedupDecision` handles merge/update/skip but doesn't model explicit contradictions. ELL requires bidirectional evidence links (support + counterevidence) to drive revision decisions.

### 3. No Immutable Versioning with Lineage
TencentDB uses a monotonic `version` field but old records are deleted from SQLite (JSONL is cleaned periodically). ELL requires **immutable** concept versions with full lineage (revises, supersedes, merges, splits) for historical reasoning.

### 4. No Deletion Cascade
TencentDB's memory-cleaner removes old JSONL entries. ELL requires a privacy-compliant deletion cascade that propagates to derived concepts and leaves audit trails.

### 5. No Outcome/Feedback Loop
TencentDB doesn't track whether retrieved memories actually improved decisions. ELL requires `Application` + `Outcome` records to close the learning loop.

### 6. No Association Layer
TencentDB doesn't create typed links between episodes (semantic, temporal, causal, contradiction). ELL requires this for reflection triggering and clustering.

### 7. No Preregistered Evaluation Protocol
TencentDB reports a single benchmark (PersonaMem +59%). ELL preregisters concept correctness, evidence precision/recall, scope accuracy, revision latency, calibration (Brier score, ECE), transfer, and cost.

## Where TencentDB Is Useful for ELL

### As an L0 Ingestion Layer
TencentDB's L0 recorder is battle-tested for capturing agent conversations. ELL could use it (or its data format) as the raw episode store without reimplementing conversation capture.

### As an L1 Extraction Pipeline
TencentDB's L1 extractor uses LLM-powered scene segmentation + memory extraction in a single call, followed by batch dedup. This is a well-architected extraction pipeline that ELL could adapt (replacing their LLM calls with our model-agnostic interface).

### As a Retrieval Backend
TencentDB's hybrid retrieval (BM25 + embedding + RRF) with fixed token budgets is a solid retrieval strategy. ELL could use it as the retrieval backend while keeping its own concept lifecycle on top.

### As a Multi-Tenant Access Control Layer
TencentDB's three-dimensional isolation (`teamId`/`userId`/`agentId`) with ACL is more mature than ELL's planned access model. ELL could adopt this pattern.

## Recommended Integration Strategy

### Option A: Use TencentDB as a Subsystem (Recommended)
```
TencentDB Agent Memory (L0 + L1 extraction + retrieval)
    ↓ (raw episodes + extracted memories)
ELL Core (Association layer + Reflection + Concept lifecycle + Evaluation)
```

**Pros:**
- Leverages battle-tested conversation capture and extraction
- ELL focuses on what makes it unique: evidence-grounded concepts with lifecycle
- TencentDB handles the operational burden of storage and retrieval

**Cons:**
- TypeScript runtime (Node.js ≥ 22) doesn't match ELL's Python stack
- Requires an adapter layer between TencentDB's JSONL/SQLite and ELL's SQLAlchemy models
- TencentDB's LLM coupling conflicts with ELL's model-agnostic principle

### Option B: Borrow Concepts, Build Own
Extract the useful patterns from TencentDB (scene segmentation, hybrid retrieval, three-dimensional isolation) and implement them natively in ELL's Python stack.

**Pros:**
- Full control over data model and lifecycle
- No external dependencies beyond PostgreSQL/pgvector
- Consistent with ELL's model-agnostic principle

**Cons:**
- More implementation work
- Loses TencentDB's battle-tested extraction pipeline

### Option C: Hybrid — Use TencentDB for L0/L1, Build ELL on Top
Keep TencentDB running as a sidecar for conversation capture and memory extraction. Build ELL's Association, Reflection, Concept, and Evaluation layers as a separate Python service that reads from TencentDB's output.

```
┌─────────────────────────────────────────────────────────┐
│  TencentDB Agent Memory (TypeScript/Node.js)            │
│  ┌──────────┐  ┌───────────┐  ┌─────────────────────┐  │
│  │ L0       │→ │ L1        │→ │ SQLite + JSONL      │  │
│  │ Capture  │  │ Extract   │  │ (retrieval backend) │  │
│  └──────────┘  └───────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓ (exported memories)
┌─────────────────────────────────────────────────────────┐
│  ELL Core (Python/FastAPI)                              │
│  ┌──────────┐  ┌───────────┐  ┌─────────────────────┐  │
│  │ Association│→│ Reflection│→│ Concept Lifecycle   │  │
│  │ Layer    │  │ Engine    │  │ (proposed→retired)  │  │
│  └──────────┘  └───────────┘  └─────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Evaluation (synthetic benchmark + calibration)    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Recommendation

**Go with Option C (Hybrid) for now, with a migration path to Option B.**

TencentDB Agent Memory is valuable for:
1. **L0 conversation capture** — battle-tested, handles edge cases
2. **L1 memory extraction** — scene segmentation + batch dedup works well
3. **Hybrid retrieval** — BM25 + embedding + RRF with token budgets

But ELL must own:
1. **Association layer** — typed links between episodes (not in TencentDB)
2. **Reflection engine** — provisional interpretations with uncertainty (not in TencentDB)
3. **Concept lifecycle** — immutable versions with full lineage (not in TencentDB)
4. **Evaluation protocol** — preregistered benchmarks with calibration (not in TencentDB)
5. **Model-agnostic interface** — no single LLM coupling (TencentDB requires LLM API)

The TypeScript/Node.js dependency is the biggest friction point. If ELL can write a thin adapter that exports TencentDB's L1 memories into ELL's Python data model, the hybrid approach is defensible. Otherwise, borrowing the patterns and implementing natively (Option B) keeps the stack consistent.

---

**Next step:** If proceeding with integration, implement a `TencentDBAdapter` that reads L1 memories from TencentDB's SQLite/JSONL and maps them to ELL's `Evidence` model. This is a 1-2 day implementation effort.
