# ADR 0004: Supervise Codex account access behind a provider adapter

- Status: Accepted
- Date: 2026-08-09

## Context

ELLChat originally supported a deterministic local provider and a direct OpenAI
Responses API adapter. The latter requires an API key and cannot treat a consumer
ChatGPT subscription as an API credential. Codex, however, documents an app-server
protocol for embedded clients, including account inspection and a browser-based
ChatGPT login flow. The installed Codex CLI can then execute authenticated turns.

ELL must add this capability without reading Codex tokens, importing user-wide
Codex configuration, enabling workspace mutations, or making Codex thread identity
canonical. The local source/event/episode records remain authoritative.

## Decision

Add a distinct `CodexCLIProvider` behind the existing `ChatProvider` port.

1. Discover the Codex executable from an explicit `ELL_CODEX_PATH`, the process
   `PATH`, or documented common installation locations.
2. Inspect authentication using `codex login status`.
3. Start ChatGPT browser login through `codex app-server` and its documented
   `account/login/start` JSONL method. Codex owns the callback and token lifecycle.
4. Execute chat turns through `codex exec` with `--ignore-user-config`,
   `--ignore-rules`, `--ephemeral`, `--sandbox read-only`, and approval policy
   `never`.
5. Send the ordered local ELLChat transcript on each turn. Do not depend on a
   provider thread as the only copy of conversation state.
6. Parse only final `agent_message` JSONL items into the provider stream. Never
   capture reasoning, tool events, authentication data, or Codex session files as
   canonical ELL evidence.

The direct OpenAI API-key adapter remains separate. Selecting Codex never reads the
OpenAI key stored by ELLChat, and selecting OpenAI never reuses Codex credentials.

## Consequences

- A user can connect a supported ChatGPT account without placing its tokens in
  ELLChat or the episode files.
- Ignoring user Codex configuration prevents personal MCP servers, plugins, project
  instructions, and writable agent policies from silently entering ordinary chat.
- Ephemeral execution currently returns the final assistant message rather than
  token-level deltas. The `AsyncThrowingStream` provider boundary remains stable for
  a later long-lived app-server transport.
- Each turn sends the bounded local transcript, so cost grows with conversation
  length. Persisted provider thread IDs may be added later as optional metadata,
  never as domain identity.
- Live success depends on an installed compatible Codex CLI, an authenticated
  account, network access, and model availability. Unit tests use protocol fixtures
  and never consume account quota.
