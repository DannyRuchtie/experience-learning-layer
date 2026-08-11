# The persistence gap is a doctrine mismatch, not missing wiring

**Found:** 2026-08-11, Darwin, while scoping "wire `ELLCore` to SQLite so the notebook survives restart".
**On:** `main` @ `e2afc65`.

## The surface problem

`ELLCore` runs entirely in memory. `ELLCore.__init__` accepts only `InMemoryStore`, `core.py` never
imports `substrates`, and `SQLiteSubstrate` has no references outside its own module. Nothing survives
process exit, and a real archive would not fit.

That looked like a mechanical shim: wrap the `Substrate` protocol in a mapping and widen a type hint.
`ELLCore` uses its store through a small surface — `[key]` get and set, `.get`, `.items`, `in`, and an
append-only `audits` list.

## The actual problem

**`SQLiteSubstrate.put` raises `CanonicalCollisionError` if an existing key is written with a
different payload.** Canonical objects are write-once by design. But `ELLCore` mutates canonical
objects in place, in three lifecycle transitions:

| site | what is rewritten |
|---|---|
| `review_reflection` | the `Reflection`, with a new `review_state` |
| `commit_concept` | the **prior** `ConceptVersion`, stamped `SUPERSEDED` with a `valid_to` |
| `invalidate_source` | the `SourceArtifact`, with `content` cleared and `tombstoned` set |

All three are legitimate transitions. All three would raise against the substrate. So the two halves
of the system disagree about whether canonical state is mutable, and the in-memory store hid it —
dicts permit rewriting, so nothing ever objected.

Only the third has a substrate equivalent: `tombstone`. The first two have none.

## Why this is worth more than a shim

The paper's doctrine is append-only evidence with immutable versioned concepts and preserved lineage.
Measured against that doctrine, **the substrate is right and `ELLCore` is wrong.** Marking a prior
concept version `SUPERSEDED` by editing it is exactly the pattern ELL exists to argue against: the
record of what was believed at the time is altered rather than closed.

This is the same shape as the leaks found earlier today — a property everyone assumed held, which no
test asserted, and which only became visible when something independent refused to go along with it.

## Options

1. **Give the substrate an explicit `replace`.** Cheapest, and it weakens write-once, which is the
   one property making the storage layer trustworthy.
2. **Stop mutating in `ELLCore`.** Review becomes an appended fact rather than an edit; supersession
   becomes a new record closing the prior version rather than a rewrite of it; current state is
   derived. Consistent with the doctrine, and it makes the audit trail real rather than nominal.
3. **Key by state version**, so each transition is a distinct immutable object.

**Recommendation: option 2**, with 3 as the mechanism where a stored transition is needed. It is more
work than 1 and it is the only one that leaves the paper's central claim true at the storage layer.

Not decided unilaterally — this changes `ELLCore`, which is the governance spine and the most tested
module in the repository. It wants review before implementation.

## Consequence for sequencing

"Make the notebook survive being closed" is not a small task ahead of the personal-archive work. It
is a design decision about whether canonical state is genuinely immutable.

The **read-only dry run over a personal archive is unaffected** and can proceed first: it retains
nothing, so it never writes canonical state and never meets this problem. Retaining anything from
real data stays blocked until persistence is settled — and now for a better reason than "SQLite is not
wired."
