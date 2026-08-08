# ADR 0003: Treat live chat as a write-ahead episode connector

- Status: Accepted
- Date: 2026-08-08

## Context

ELL needs a first-party input mechanism for live conversations. The interface should
feel like an ordinary chat client, support replaceable model providers, and produce
the same canonical source, event, and episode records as imported histories. If a
provider owns the only copy of the conversation, provenance, provider switching,
forgetting, and reproducible learning all become weaker.

The previously reviewed
[TencentDB Agent Memory](https://github.com/Tencent/TencentDB-Agent-Memory) project
now provides a local L0-L3 pipeline, readable intermediate artifacts, SQLite plus
hybrid retrieval, and host adapters. Google also offers a managed Vertex AI Agent
Engine Memory Bank. Both are useful comparison systems, but neither may define
ELL's canonical evidence or memory lifecycle. Tencent's progressive extraction is
a benchmark and adapter candidate. Google's hosted memory is a later optional
provider for deployments whose egress policy permits it.

## Decision

Add a macOS-first SwiftUI client named `ELLChat` as the first Phase 1 connector.
For every completed turn it:

1. writes the user's exact message as an immutable `SourceArtifact` and
   `ExperienceEvent` before contacting a provider;
2. streams the selected provider response;
3. writes the final assistant response as another source and event;
4. closes the ordered pair as a deterministic `Episode`;
5. keeps the mutable chat-history file as a rebuildable UI projection.

The app writes portable JSONL locally. Stable UUIDv5 identities use the same ELL
namespace and name construction as the Python kernel. Credentials live in macOS
Keychain and never enter source, event, episode, projection, or log files.

`ChatProvider` is the client-side provider port. The deterministic mock is the safe
default. The first remote adapter uses the OpenAI Responses API. Codex is reserved
for a distinct workspace-agent adapter, and Anthropic is reserved for a later chat
adapter. Provider conversation IDs remain metadata rather than domain identity.

The Python `EpisodeCaptureService` remains the executable reference policy: source
existence and workspace scope are checked before event capture; episode membership
must be single-workspace, single-session, and chronologically ordered; replay is
idempotent. The app's JSONL records use these existing versioned contracts.

## Consequences

- An interrupted provider call still leaves the user input as attributable evidence;
  it does not create a falsely completed episode.
- Provider switching can rebuild context from local events instead of depending on
  one vendor's thread state.
- Chat capture can ship before model-driven learning; extraction still produces
  typed candidates that deterministic policy must govern.
- JSONL is intentionally the first persistent adapter. SQLite, TencentDB, vector
  retrieval, or hosted memory may be benchmarked behind ports without migration of
  canonical semantics.
- Live API behavior is not proven until a user supplies a credential through
  Keychain. The mock path remains sufficient for deterministic builds and tests.
