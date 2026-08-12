# Remaining work, and who owns it

**Date:** 2026-08-12. **Owner:** Darwin (ELL Lead). **State:** `main` @ `acff8df`.

## The reordering that matters

The plan as of last night ran: finish validating the instrument → build the learner → run the study.
That order is probably wrong, and the reason is a dependency nobody spotted until late.

Validating the primary stratum requires showing that `far` is solvable by **some** non-oracle method
that is not ELL — otherwise the acceptance criterion is circular, valid only if the hypothesis is
true. The candidate is the self-managed flat-file baseline. But if that baseline is faithful to Chen
et al., **a model writes the notes** — which makes it a Phase 3 condition. A deterministic imitation
would fail `far` for structural reasons and teach us nothing.

**If that reading is right, the instrument cannot be finished before the learner exists.** Phase 3
moves from "next phase" to "critical path", and Track B below runs first.

**Open question, and it gates the plan:** Scholar to confirm the Chen et al. flat-file design. I have
not read the primary source; Scholar has the citation.

## Track A — Finish the instrument

| # | work | owner | blocked by |
|---|---|---|---|
| A1 | Confirm whether the flat-file baseline requires a model | **Scholar** | — |
| A2 | Build the flat-file comparator | **Forge** | A1; possibly Track B |
| A3 | Decide route (a) rebuild vs narrowed claim if `far` proves ungradeable | **Darwin** + Reviewer | A2 |
| A4 | Amend A1 criterion — proposed, not applied | **Darwin**, review by Reviewer + Scholar, sign-off Danny | — |
| A5 | Derive tier sizing from development between-rule variance | **Forge** | A2 |
| A6 | Tag the immutable v0.8 release | **Darwin** | A5 |

Pre-committed already: if the flat-file clears `far`, the gate is non-circular and Phase 1 proceeds.
If it fails, route (b) was the wrong call and the answer space needs rebuilding.

## Track B — Build the learner (the actual research)

Protocol written: `research/PHASE3_PROTOCOL.md`. No code exists.

| # | work | owner |
|---|---|---|
| B1 | Proposer: model reads permitted episodes, emits `Reflection` objects only | **Forge** |
| B2 | Deterministic validator: the eight reject codes, before any review | **Forge** |
| B3 | Frozen prompts as hashed artifacts; two open model families | **Forge** + Darwin |
| B4 | Promotion rule: frozen K episodes / M days, deterministic confidence | **Darwin** sets, Forge implements |
| B5 | Adversarial review of the quarantine boundary | **Reviewer** |
| B6 | Development sweeps; rejection-rate profile per model family | **Forge** |

B5 matters more than its size suggests. Every leak found so far was a join between individually
defensible fields, and the proposer is the first component with a genuine incentive to be persuasive.

## Track C — The personal prototype

Runs parallel; does not gate the research.

| # | work | owner | blocked by |
|---|---|---|---|
| C1 | ChatGPT export importer → `SourceArtifact` / `Episode` | **Forge** | Danny: file path + exclusion list |
| C2 | Read-only dry run: show what would be retained, retain nothing | **Forge** | C1, B1, B2 |
| C3 | SQLite wiring: mapping over the `Substrate` protocol, durable transition logs | **Forge** | — (unblocked as of `acff8df`) |
| C4 | Review surface: approve/reject, evidence shown before claim | later | C2 |

**Hard gate:** nothing from a personal archive is *retained* until C3 lands and deletion is exercised
against real storage. The dry run is exempt because it keeps nothing.

## Track D — Publication

| # | work | owner |
|---|---|---|
| D1 | Claim-scope wording audit against v0.8 `claim_scope` | **Scholar** |
| D2 | Narrow the novelty claim to the revisable-claim contribution | **Scholar** |
| D3 | Finish the citation verification queue | **Scholar** |
| D4 | Keep the published site current | **Darwin** |
| D5 | Declare the self-experimentation design if the pilot runs | **Scholar** + Darwin |

## Decisions needed

**1. Does the prototype compete with the research for Forge's time?** Forge is the only implementer
and Tracks B and C both need them. My recommendation: **B first**, because it is the critical path for
both — the learner is also what the dry run needs. C1 and C3 are small enough to interleave.
**Danny's call, because it is a priority question, not a technical one.**

**2. If `far` proves ungradeable, do we rebuild the answer space (route a) or narrow the claim
further?** Mine, with Reviewer. Not yet due — A2 answers it.

**3. Two open model families: which?** Mine. Deferred until B1 is scoped; the choice should follow
what the validator needs, not vendor preference.

## On "the most scalable solution"

Three things actually determine that, and only one is a coding decision:

- **C3, the storage layer.** Everything is in memory today. This is the real scalability limit and it
  is now unblocked.
- **Provider neutrality.** Already a design property; B3's two model families are what turns it from
  a claim into a tested one.
- **The append-only doctrine.** Landed last night. It is what lets the system scale *in trust* rather
  than only in size — history stays reconstructible as the store grows.

The honest caution: scalability work on a system whose central claim is untested optimises something
we do not yet know is worth optimising. The order in this plan reflects that.

## Unchanged

No empirical result exists. None of H1–H7 has been tested. Nothing is frozen or tagged.
