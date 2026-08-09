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

Database, vector, and MCP work deliberately follows this proof.

## Phase 1 live capture preview

`ELLChat` is a native macOS chat wrapper that writes each message to local,
provider-neutral source and event JSONL before provider processing, then closes a
completed user/assistant turn as a deterministic episode. It includes a local mock
provider, an OpenAI Responses API streaming adapter, Keychain credential storage,
an account-backed Codex CLI adapter with native ChatGPT browser sign-in, and a
reserved Anthropic provider seam. Codex owns its authentication tokens; ELLChat
does not read or persist them.

```bash
make app-test
./script/build_and_run.sh --verify
```

The mutable chat history is a UI projection. Canonical capture files live under
`~/Library/Application Support/ExperienceLearningLayer/Chat/` when the app runs.

## Quick start

```bash
make install
make paper
make test
```

## Requirements

- Python 3.9+
- ReportLab (installed by `make install`)
- Codex CLI (optional, for ChatGPT-account-backed Codex conversations)

## Project structure

See `AGENTS.md` for development rules and commands. Architecture decisions are in
`docs/adr`. The repository remains paper-first while its Phase 1 surface now includes
the small live-chat capture client and append-only local episode adapter.
