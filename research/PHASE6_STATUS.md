# Phase 6 status

Status: adapters and consent protocol implemented; no external or human study run.

External benchmark boundaries:

- MemoryArena adapter for its documented JSONL `id`, `questions`, `answers`, and
  `backgrounds` structure;
- normalized LoCoMo-Plus adapter for cue-trigger constraint tasks;
- normalized Mem2ActBench adapter for memory-grounded tool calls;
- mandatory local file, exact dataset hash, source URL, citation, version, and SPDX
  licence declaration before any package can enter a run.

The adapters do not download datasets automatically. MemoryArena documents its dataset
as CC-BY-4.0 at <https://memoryarena.github.io/>. LoCoMo-Plus and Mem2ActBench packages
must be checked against the exact local release and licence before use; paper availability
alone is not treated as data-use permission.

Pilot boundary:

- protocol readiness requires an ethics-review reference, inspection, correction,
  scoped deletion, incident response, and a tested withdrawal path;
- enrollment requires signed, time-bounded, purpose-specific consent;
- provider egress is denied unless both protocol and participant explicitly allow it;
- event receipts retain pseudonym, purpose, hash, egress state, and time, not raw content;
- withdrawal blocks subsequent events.

Current evidence: zero verified external packages and zero consented participants. No
external-validity, user-benefit, or safety-transfer claim has been made.

