# Experience Learning Layer

An open, local-first learning and memory layer that turns accumulated experience
into evidence-backed, revisable concepts and scoped context for people,
applications, and AI agents.

The product and technical foundation is [docs/L_ARCHITECTURE.md](docs/L_ARCHITECTURE.md).
The complete evolving research paper lives in [paper/ELL_Paper.md](paper/ELL_Paper.md),
with a reproducible current PDF under `output/pdf`.

## Phase 0 proof

The provider-neutral in-memory kernel currently demonstrates:

- versioned Pydantic and JSON Schema contracts for sources, events, episodes,
  candidates, memories, audit events, retrieval requests, and evidence packets;
- deterministic source/event/episode IDs and a fixture-backed mock model provider;
- evidence, workspace, sensitivity, authority, correction, contradiction,
  idempotency, optimistic-concurrency, and forgetting invariants;
- budgeted lexical retrieval with explanations and optional exact evidence;
- a versioned synthetic golden corpus under `evals/golden/v1`.

Database, vector, provider, MCP, and chat UI work deliberately follows this proof.

## Quick start

```bash
make install
make paper
make test
```

## Requirements

- Python 3.9+
- ReportLab (installed by `make install`)

## Project structure

See `AGENTS.md` for development rules and commands. Architecture decisions are in
`docs/adr`. The repository is intentionally scoped to the living paper and its
provider-neutral Phase 0 proof; persistence, connectors, model SDKs, and clients are
future phases.
