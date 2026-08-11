# Phase 3 protocol — model-assisted learning under quarantine

**Status:** protocol draft, no implementation. **Author:** Darwin (ELL Lead). **Date:** 2026-08-11.
**Grounded on:** `main` @ `f20128f`, against the real `ELLCore` API.

Phase 3 was the only phase with no written protocol, while being the phase where ELL's actual
contribution lives. Every other phase either supports it or measures it.

## What Phase 3 is, and why it is the real test

Phases 0–2 built a governed vault: evidence with provenance, versioned revisable concepts, scoped
retrieval, deletion closure. But every reflection so far has been handed in by a fixture. Nothing has
ever *proposed* a lesson.

Phase 3 adds the proposer — a language model reading episodes and suggesting what might be learned.
That is also precisely where the failure mode ELL exists to prevent enters the system: **a confident,
plausible, unsupported generalisation that nobody can trace or challenge.** So Phase 3 is not
"add an LLM to the pipeline." It is the experiment.

The thesis under test: *governance can make model-generated learning safe enough to be useful,
without discarding the model's ability to generalise.* Both halves are falsifiable. If governance
rejects nearly everything, the system is safe and useless. If it admits unsupported claims, it is
useful and unsafe. Either outcome is a result and both are reportable.

## The governance boundary

**The model proposes `Reflection` objects. It does nothing else.**

| the model may | the model may never |
|---|---|
| read permitted episodes within one workspace | write a `ConceptVersion` |
| propose a `statement`, `reflection_type`, `scope` | set `confidence` |
| cite `support` and `counterevidence` by record id | decide promotion |
| express `uncertainty` | review its own proposal |
| — | see any other workspace, deleted evidence, or evidence later than the cutoff |

`ELLCore.quarantine_reflection` is the only entry point available to it, and `review_state` enters as
quarantined by construction. Concepts are created solely by `commit_concept`, which requires
`validated_reflection_ids` — reflections that have already passed validation and review.

This is a structural boundary, not a policy. After four leaks today, all of which were joins between
individually defensible fields, the boundary is stated in terms of *what information can reach the
proposer*, and enforced by the same projection the benchmark policies use.

## Stage 1 — deterministic validation, before any review

A proposed reflection is checked by code, never by a model, and it is checked **before a human sees
it.** A reviewer who reads a fluent, confident proposal is already anchored; the deterministic gate
exists to prevent persuasion from doing work that evidence should do.

Every check is a hard reject with a stable failure code:

| code | check |
|---|---|
| `span-unresolvable` | every `support` and `counterevidence` id resolves to a real record via `resolve_evidence` |
| `foreign-workspace` | all cited evidence is in the reflection's workspace |
| `deleted-evidence` | no cited record is deleted or permission-denied |
| `future-evidence` | all cited evidence precedes the reflection's `observed_time` |
| `single-episode-generalisation` | support spans at least **K distinct episodes across M distinct days** |
| `unbounded-scope` | `scope` is non-empty and drawn from the controlled vocabulary |
| `counterevidence-not-searched` | a counterevidence search was executed and its result recorded, **including when empty** |
| `sensitive-inference-unflagged` | inferences over sensitive categories carry an explicit flag |

`K` and `M` are preregistered before any run and are the primary knob distinguishing "learned a
pattern" from "over-read one conversation." They are set on development and frozen.

**A failed reflection is retained, never silently dropped.** Failure codes and rates are reported per
model family. A high rejection rate is a finding about the proposer, not an embarrassment to hide —
and a rejection rate near zero is itself suspicious and must be investigated before the sealed run.

## Stage 2 — review

Reviewed via `ELLCore.review_reflection(..., accept: bool, actor_id: str)`.

- **Research runs:** review is a deterministic policy, so the confirmatory result does not depend on
  human judgement that cannot be replayed. The policy is frozen with the prompts.
- **Pilot runs (Danny's own data):** review is human, and the interface must show the cited spans
  *before* the proposed statement. Ordering matters; evidence first, claim second.
- **A second model family may screen, but may never promote.** Model agreement is recorded as a
  diagnostic, never as authority. Two models agreeing on an unsupported claim is a correlated error,
  not corroboration.

## Stage 3 — promotion to a concept

`commit_concept` requires `validated_reflection_ids`. Promotion criteria are deterministic and
preregistered:

1. the reflection passed Stage 1 and was accepted in Stage 2;
2. support meets the frozen `K` episodes / `M` days threshold;
3. **counterevidence was searched, and if any exists the concept must either narrow its `scope` to
   exclude it or not promote at all.** Promoting over unresolved counterevidence is prohibited;
4. `scope`, `conditions` and `valid_from` are all set;
5. **`confidence` is computed by a frozen deterministic rule** from support and counterevidence
   counts and their recency. The model never sets it. A model-assigned confidence is a fluency
   measurement wearing a probability's clothing.

Concepts remain revisable by construction: `parent_versions` preserves lineage, `valid_to` closes
prior validity, and outcomes recorded through `record_outcome` can trigger revision or retirement.

## Model conditions

- **Two open model families**, so a result is not an artifact of one vendor's habits. Provider
  neutrality is a claim in the README and this is where it gets tested.
- Frozen model identifier, revision, serving software, sampling parameters and seed where the
  provider exposes one. All digests recorded in the run manifest.
- **Prompts are frozen artifacts with content hashes**, developed only on the development partition.
- Stochastic conditions are run **n times per configuration** with the interval reported. A single
  sample from a stochastic proposer is an anecdote.

## Freezing, and its relationship to the sealed run

Everything above is developed and tuned on **development data only**: prompts, `K`, `M`, the review
policy, the confidence rule, the number of repeats. All are frozen and hashed before the sealed run
opens. **The sealed run tunes nothing** — one frozen configuration, one recorded run, failures
retained.

This is the constraint the whole preregistration exists to protect, and Phase 3 is where it is most
tempting to break, because prompt iteration feels like engineering rather than analysis. It is not.
A prompt tuned against sealed performance is a hyperparameter fitted to the test set.

## What would falsify Phase 3

Preregistered, so the answer cannot be chosen after the fact:

- **Governance is unusable** — validation rejects so large a share of proposals that too few concepts
  form to affect any task. Reported as *governance too strict for model-generated learning at this
  threshold*, with the rejection profile.
- **Governance is porous** — unsupported generalisations pass validation and review. Measured against
  the existing unsupported-generalisation gate. This is the **unsafe** verdict and it outranks any
  utility result.
- **Concepts form but do not transfer** — well-supported concepts commit, and far-transfer does not
  improve over the strongest eligible comparator. The concept layer is *unsupported for the tested
  conditions*, and the research plan already commits to adopting the simpler method in that case.
- **Model-family dependence** — the two families disagree substantially in what survives governance.
  That bounds any general claim to the family tested and must be reported, not averaged away.

## Dependencies, honestly

Phase 3 cannot start its confirmatory arm until the instrument can grade the primary stratum. As of
today, `far` has no robust non-oracle comparator, and whether one exists is an open question being
tested with a self-managed flat-file baseline. Phase 3 development work — proposer, validator,
prompts — does **not** depend on that and can proceed in parallel.

Phase 3 also unblocks the pilot path: the dry-run inspection over a personal archive is exactly this
proposer plus Stage 1 validation, with retention disabled.

## What this document is not

A design for the proposer's prompts, or a claim that any of it works. Nothing here has been
implemented. It fixes the rules before the code exists, which is the only order that makes the result
mean anything.
