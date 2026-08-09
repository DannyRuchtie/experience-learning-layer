# Phase 1 status

Status: deterministic reference slice implemented; exit not yet claimed.

Implemented evidence:

- deterministic chronological streams of 50, 200, and 1,000 records with 30,
  120, and 640 paired tasks respectively;
- paraphrases, supporting cases, contradictions, scoped exceptions, correlated
  evidence, change points, delayed outcomes, permission denials, deletions, and distractors;
- train, development, and sealed partitions with a committed sealed seed;
- development generation that never materialises sealed cases;
- no-memory, maximum-context, BM25, exact-vector, fixed fusion, rolling-summary,
  and direct-insight baselines;
- canonical dataset and configuration hashes;
- application receipts, selected-record traces, evaluator judgments, and total-token costs;
- deterministic manifests use the replay's logical start time; confirmatory wall-clock,
  latency, and hardware traces remain separate measured fields rather than fabricated values;
- deterministic tests proving identical seeds reproduce identical data and results;
- a known-good deterministic policy that separates from the deliberately broken
  no-memory condition.

Remaining exit evidence:

- run the artifact on two independently provisioned clean machines and publish both logs;
- freeze actual open model identifiers, serving software, prompts, and stochastic intervals;
- run the development-only power check against observed benchmark variance;
- have an independent reviewer verify that scope labels and deterministic policies do not
  leak gold latent rules into an eligible confirmatory baseline;
- tag the generator, configuration, and resulting baseline artifacts.

The sealed partition must not be opened to satisfy these development gates.
