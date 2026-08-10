# Internal Review — *From Episodes to Revisable Concepts* v0.6

Reviewed 10 August 2026 against commit state of `main`. Scope: all 16 chapters, `references.qmd`,
`research/research-contract-v0.6.json`, `src/ell/statistics.py`, `schemas/v0.6/`.

---

## Summary verdict

The paper's core move is right and unusually disciplined: it refuses to claim novelty for
abstraction, names one confirmatory outcome, and pre-commits stop conditions. Most agent-memory
papers do not do this. The self-criticism in Chapter 10 is stronger than the criticism the paper
would receive from a reviewer, which is a good sign.

The problem is that **the preregistration is not yet as rigorous as the prose claims it is.** Seven
gates must all pass for a "supported" verdict, and only one of them has a sample-size
justification. Several gates cannot be computed for the comparator at all, which means they are not
comparative gates. Under the paper's own framing this is the difference between a preregistration
and a statement of intent.

Second-order problem: the manuscript is ~16k words with roughly 15–20% redundancy, has no
bibliography tooling, and renders all of its mathematics as broken plain text. That combination
will cost it credibility before a reader reaches the argument.

Nothing here requires abandoning the design. The fixes are: power the guardrails, add two missing
experimental conditions, cut a chapter, and do a mechanical cleanup pass.

**Priority order:** A1 → A2 → A12 → A6 → C1 → C2 → B3 → everything else.

---

# Part A — Methodology

## A1. Six of the seven decision gates have no sample-size justification — CRITICAL

`research-contract-v0.6.json` contains exactly one power block:

```
/power/target_absolute_effect        = 0.05
/power/assumed_discordant_pair_rate  = 0.20
/power/minimum_power                 = 0.80
/power/paired_tasks_per_condition    = 640
```

That powers the **primary transfer** gate only. The other six gates — unsupported generalisation,
evidence quality, change adaptation, cost efficiency, governance invariants, replication — are
assigned thresholds with no variance model and no N.

This matters most for the **unsupported-generalisation non-inferiority gate**, because that gate is
what makes the primary claim safe. Chapter 11 requires the upper bound of the paired 95% CI to sit
below a +2-point margin. I recomputed what that needs:

| Discordant-pair rate on scope violations | N for the CI to be able to clear +2pt | N for 80% power at true diff = 0 |
|---|---|---|
| 0.05 | 480 | 981 |
| 0.10 | 960 | 1,962 |
| 0.20 | 1,921 | 3,924 |
| 0.30 | 2,881 | 5,887 |

At 640 paired tasks the gate is only decidable if scope-violation disagreements are rare
(≈5% discordance). If they occur at anything like the rate assumed for the primary outcome (0.20),
**640 tasks cannot clear a 2-point non-inferiority margin even when the true difference is exactly
zero.** The gate would then fail for reasons that have nothing to do with ELL's behaviour, and the
verdict would default to "partially supported" as an artefact of sample size.

**Fix.** Either (a) add a `/power/unsupported_generalization` block with its own discordance
assumption and N, sizing the study on `max(N_primary, N_noninferiority)`; or (b) widen the margin
to something 640 pairs can actually decide and justify the wider margin on cost-of-error grounds;
or (c) reclassify the gate as a diagnostic that is reported with its interval but does not gate the
verdict. Option (a) is the honest one. Do the same for evidence quality (A9) and change adaptation.

## A2. The study is underpowered for its own success label — CRITICAL

"Supported" requires all seven gates to pass simultaneously. Conjunctive testing needs no
multiplicity correction for Type I error — that part is fine, and worth stating explicitly in the
paper — but it compounds Type II error:

| Power per gate | P(all 7 pass) |
|---|---|
| 0.80 | 0.21 |
| 0.85 | 0.32 |
| 0.90 | 0.48 |
| 0.95 | 0.70 |

At the declared 80% power per gate, a *fully correct* ELL has roughly a **1-in-5 chance** of earning
a "supported" verdict. The paper would then record its own hypothesis as unsupported four times out
of five. Chapter 11's rejection conditions become close to self-fulfilling.

**Fix.** Add a *conjunctive power* target to Chapter 11 and the contract — e.g. "the design targets
≥70% probability of a supported verdict under the assumed true effect, requiring ≥95% power per
mandatory gate." Then size N accordingly. Alternatively, split the gates into *confirmatory*
(transfer + unsupported generalisation) and *release-blocking but non-confirmatory* (governance,
cost, replication), and state that the scientific verdict rests on the first pair. That is a
defensible reframing and probably the cheaper one.

## A3. 640 leaves a 2.4% margin over the required 625, while exclusions are permitted — MAJOR

`minimum_paired_sample_size()` returns 625 under Connor's formula; I verified it independently
(exact McNemar power at δ=0.05, p_d=0.20, two-sided α=0.05 needs ~123 discordant pairs → N≈616).
The math is correct.

But two things sit uncomfortably together:

1. **The margin is 15 tasks.** If the observed discordant rate is 0.25 rather than 0.20, the
   requirement rises to 775 and the study is underpowered. If it is 0.30, 934. Discordance is not
   under your control and will not be known until the sealed run.
2. **Chapter 11 permits exclusions** (corrupt source artifacts, duplicate task identifiers). Any
   exclusion drops N below the threshold.

**Fix.** Raise to 768 or 1,024 paired tasks (both are clean multiples of your 640/120/30 generator
tiers and give headroom to p_d = 0.25–0.30 plus exclusions). Cost is generator time, not scientific
compromise. State the inflation factor and its reason in the contract.

## A4. The 0.20 discordant-pair rate is a hardcoded default with no empirical basis — MAJOR

It appears as a Python default argument (`discordance: float = 0.20`) and as a contract constant.
Nothing in the paper justifies it. Every N in the design depends on it.

**Fix.** Run a development-partition pilot on the already-built Phase 1 baselines to estimate the
discordant rate between the two strongest simple baselines, and cite that number. You have the
machinery; this is a day of compute. If the estimate is unavailable, present N as a sensitivity
table across p_d ∈ {0.15, 0.20, 0.25, 0.30} rather than a single figure.

## A5. Several gates are not comparative, because the comparator has no such objects — MAJOR, conceptual

This is the finding I would push hardest on in review.

- **Evidence quality** (support precision ≥0.95, counterevidence recall ≥0.90) presupposes cited
  support sets. A no-memory baseline, BM25 over raw episodes, or a rolling summary has no
  `EvidenceLink`. The metric is computable for ELL and undefined for most of conditions 1–7.
- **Change adaptation** ("90% of affected concepts contested or revised within two contradictory
  episodes") presupposes `ConceptVersion` objects. Baselines have no concepts to contest.
- **Governance invariants** (lineage, deletion cascade, workspace isolation) presuppose the ELL
  data model.

Chapter 11 presents these as gates in a comparative table alongside the primary transfer gate,
which reads as though ELL is being held to a standard *relative to* the comparator. It is not. Three
of seven gates are **absolute self-consistency thresholds on ELL alone**. That is legitimate — they
are safety floors — but the paper must say so, because a reviewer who notices this will read the
gate table as either confused or as quietly stacked.

**Fix.** Split the Chapter 11 table into two: *comparative gates* (transfer, unsupported
generalisation, cost efficiency, replication — all of which have a defined baseline value) and
*absolute invariants* (evidence quality, change adaptation, governance). For the absolute ones,
state the behavioural proxy that *is* measurable on baselines — e.g. post-change stale-guidance
rate is measurable for a rolling summary, so keep that as the comparative form of the adaptation
gate, and treat "concepts contested within two episodes" as an ELL-internal diagnostic.

## A6. No oracle-concept ceiling condition — MAJOR, cheap to add

The nine baselines in Chapter 7 span from no-memory up to full ELL-Core, but there is no condition
where **the gold latent concepts are injected directly** into the packet.

Without it, a null result is uninterpretable. If ELL-Core shows no transfer gain, you cannot
distinguish:

- (a) concepts don't help this answer model at all — the *usage* channel is dead; from
- (b) concepts would help, but induction quality is too low — the *induction* channel is weak.

Those two failures have opposite implications for what to do next, and Chapter 11 currently routes
both to "not supported → investigate the winning simpler baseline." In case (a) that is right. In
case (b) it is the wrong conclusion.

**Fix.** Add condition 10: *oracle concepts* — gold propositions, scope, and validity intervals
from the generator, packaged in the identical envelope under the identical budget. This is
essentially free because the generator already holds gold labels. It gives you an upper bound, makes
`ELL-Core / oracle` an interpretable induction-quality ratio, and turns a null result into a
diagnosis. Consider also condition 11: *oracle retrieval* (gold-relevant episodes, no concepts) to
separate retrieval from abstraction.

## A7. Causal attribution is confined to the limitations chapter — MAJOR

Chapter 10, criticism four, correctly identifies that an `ApplicationReceipt` proves presence, not
causation, and proposes "factorial packet ablations and randomised inclusion on eligible tasks."
Chapter 7 then does not implement this. The ablation list removes *components of the pipeline*, not
*the packet at decision time*.

**Fix.** Promote randomised packet inclusion into the Stage D design: on eligible sealed tasks,
randomise (pre-committed seed) whether the retrieved packet is delivered to the answer model. This
converts concept utility from an observational to an experimental estimate at near-zero extra cost,
and it is the single strongest methodological upgrade available to the paper. It also gives you a
manipulation check on whether the answer model reads the packet at all.

## A8. Confidence formula is not specified to preregistration standard — MAJOR

Chapter 5 gives `confidence(c) = 1/(1+exp(-z_c))` and then defines `z_c` only as "a weighted score
that increases with supporting evidence, evidence diversity, and observed application utility, and
decreases with counterevidence, age without revalidation, and validator disagreement."

That is a description of monotonicity, not a function. Six features, unspecified weights, and an
unspecified fitting procedure. Chapter 11 gates calibration (Brier, ECE) on a quantity the paper
has not defined. Chapter 4's relevance score `R(c,q)` has the same problem — six weights, "tuned on
development data," no functional form, no tuning protocol.

**Fix.** Write both out fully: exact feature definitions, exact functional form, the frozen
mandatory-baseline weights (Chapter 5 already says a fixed count-based rule is the mandatory
baseline — give its coefficients), and the dev-only fitting procedure with its objective and
regularisation. Then reference `schemas/v0.6/` for the machine-readable version. Until this exists,
"preregistered" overstates what is frozen.

## A9. Evidence-quality thresholds are point estimates with no uncertainty — MODERATE

"Support precision at least 0.95 and counterevidence recall at least 0.90" — as point estimates or
as interval bounds? At n=640 with ~3 support links per concept, the CI on a precision of 0.95 is
roughly ±0.02. A gate stated as a point estimate will be passed or failed by noise.

**Fix.** State the estimator, the denominator (per link? per concept? per decision?), and whether
the rule applies to the point estimate or the lower confidence bound. Recommend lower bound, and
raise the sample of adjudicated links accordingly.

## A10. Power computed under McNemar, inference by percentile bootstrap — MINOR but visible

`minimum_paired_sample_size()` implements Connor's McNemar formula; the declared primary analysis is
a 10,000-resample paired percentile bootstrap. These agree asymptotically, but the percentile
bootstrap is known to undercover for differences of proportions at small discordance — precisely the
regime the non-inferiority gate operates in, where the *upper bound* is the decision statistic.

Also, the interval indexing in `paired_bootstrap_interval` uses
`floor(0.025 × (B−1))` / `ceil(0.975 × (B−1))`, which is one convention among several and will
differ by a resample or two from `numpy.percentile`. Harmless, but pin it in the contract so a
replicator gets bit-identical bounds.

**Fix.** Either power the study under the bootstrap by simulation (you have the generator — 10k
simulated studies is cheap and would also give you the conjunctive power figure from A2), or switch
the non-inferiority decision to BCa or exact McNemar. Document whichever you pick.

## A11. Baseline selection on development data needs a pre-committed tie-break — MODERATE

"The strongest of conditions 3–7 is selected on development data" is the right instinct and
conservative in expectation. But if two baselines are within noise on dev, the choice materially
changes the sealed comparator, and there is no stated rule.

**Fix.** Pre-commit: (i) the exact dev metric used for selection, (ii) a tie-break rule when
candidates are within one dev standard error (recommend selecting the *cheaper* baseline, which is
the more conservative comparator for the cost gate but the weaker one for transfer — pick and
justify), (iii) whether selection is per-stream-length or global.

## A12. Hypothesis and metric inflation dilutes the confirmatory story — MODERATE

- **H4 and H6 overlap substantially.** H4 is "fewer median input tokens without reducing success";
  H6 is "reduce decision tokens, latency, and energy while preserving utility, inclusive of
  background cost." H6 subsumes H4. Merge them.
- **RQ5/H5 and the eight product-facing criteria in Chapter 7** occupy more space than the
  confirmatory metrics, then Chapter 7 and Chapter 11 both have to say they cannot establish the
  claim. Two disclaimers for material that could move to an appendix or to the Phase 6 section of
  Chapter 12.
- **There is no single table mapping RQ → hypothesis → metric → gate → phase.** Six hypotheses,
  five RQs, four metric families, seven gates, seven phases, all in prose across four chapters. A
  reader cannot currently verify that the set is coherent. I tried and could not close the loop
  between H2 and the change-adaptation gate without inference.

**Fix.** Add that mapping table to Chapter 2 or 11. It will pay for itself immediately — I expect it
will surface one or two hypotheses with no gate and one gate with no hypothesis.

## A13. Missing literature: machine unlearning — MODERATE

Deletion cascade is one of the paper's headline governance invariants, and Chapter 10 (eleventh
threat) correctly notes that an external ledger cannot prove a parametric deletion removed all
influence. But the paper cites no machine-unlearning or right-to-be-forgotten literature, which is
the field that has spent a decade on exactly that verification problem. A reviewer in the privacy
area will notice.

Similarly, Chapter 7 reports Brier score and ECE with no calibration citations, and Chapter 5's
"evidence diversity" measure has no grounding in the source-independence literature it implicitly
depends on.

---

# Part B — Argument and structure

## B1. Roughly 15–20% redundancy — MAJOR for readability

The "north star / evolving intuition / grounded, economical, sensitive to change, explainable, under
user control" formulation appears near-verbatim in **five** places: `index.qmd`, Ch 1 ¶2, Ch 4,
Ch 13 ¶3, Ch 15 ¶3. The "models interpret, deterministic code governs" formulation appears in Ch 4,
Ch 6, Ch 13, and twice as a figure caption. The provider-neutrality argument is made in Ch 3, Ch 4,
Ch 6, and Ch 13.

State each once, in its strongest location, and cross-reference.

## B2. Chapter 13 does not belong in this paper — MAJOR

Chapter 13 is 1,390 words describing an architecture the paper explicitly says is not being tested,
not implemented, and not entering the confirmatory comparison. It also contradicts its own framing:
it introduces ten memory types where ELL-Core has seven objects, and names a third packet type
(`EvidencePacket`).

The paper's greatest strength is the narrowness of its claim. Chapter 13 is the one place that
strength is undercut, because it reads as the roadmap the author actually wants to build. Move it to
an appendix titled "Deferred product architecture (not part of the confirmatory study)", or to a
separate design document in `research/`, and keep Chapter 12's "Deferred research tracks" section as
the only forward-looking content in the main body.

## B3. Related work recites rather than synthesises — MAJOR

Chapter 3 is the longest chapter (2,340 words) and is largely "System X did Y (cite)." Roughly 35
systems are described serially. The positioning table at the end groups them into six families but
does not compare them on any axis.

The paper's novelty claim is *the specific combination* of provenance + counterevidence + scope +
versioning + temporal validity + outcome feedback + deletion cascade. That claim is currently
asserted in prose and cannot be checked by a reader.

**Fix — highest-value single addition to the paper.** Replace or supplement the positioning table
with a capability matrix: rows = ~12 nearest systems (Mem0, Zep/Graphiti, Letta, Hindsight,
TencentDB, A-MEM, RMM, DCPM, GAAMA, PlugMem, ReasoningBank, ELL-Core); columns = the seven
capabilities above, plus "concept-level evaluation." Mark ✓ / partial / ✗ with a footnote per
non-obvious cell. If ELL is the only row with all eight, the novelty claim is *demonstrated* in one
glance. If it is not — which is possible for DCPM and PlugMem — you have found that out before a
reviewer did, and can narrow the claim accordingly. Either outcome is worth the work.

## B4. No worked end-to-end example in the paper — MAJOR

`examples/golden-cases.jsonl` exists and Chapter 14 lists thirteen scenario types, but no reader of
the paper ever sees one episode become one reflection become one concept, get retrieved into one
packet, produce one receipt, and get revised by one outcome. The stakeholder-consultation example in
Chapter 1 is the closest, and it stops at promotion.

**Fix.** Add a two-page worked trace — ideally the temporal-change case, since it exercises valid
time, counterevidence, revision, and lineage at once. Show the actual JSON at each step. This is
the fastest way to make the contract feel real, and it doubles as documentation for anyone
implementing against `schemas/v0.6/`.

## B5. Three names for one object — MODERATE

`LearningPacket` (Ch 6, and the schema file), `EvidencePacket` (Ch 13), "intuition packet" (Ch 1, 4,
7, 11, 13, 15). Chapter 4 additionally gives a formal definition `I(q,t,p,b) = (C*,E*,A*,U*,X*,L*)`
whose six components do not map cleanly onto the `LearningPacket` schema's fields.

Pick one canonical type name (`LearningPacket`, since it is what the schema says), define "intuition
packet" once as its presentation at the application boundary, delete `EvidencePacket`, and make the
formal tuple match the schema field-for-field.

## B6. The abstract buries its own strongest sentence — MODERATE

The falsifiable claim — "under matched model and total-compute conditions, an evidence-governed
concept layer should improve transfer… If it does not, the concept layer is not justified" — is the
last thing in a 450-word abstract, behind four paragraphs of architecture description.

That sentence, and the fact that the paper reports no results, should be in the first two sentences.
Cut the abstract to ~250 words: the distinction (retrieval ≠ learning), the claim, the falsification
condition, the status.

## B7. Ethics chapter is under-weight relative to the paper's governance claims — MODERATE

256 words, the shortest chapter, and it is the substantive content behind a mandatory gate
("Governance invariants: 100% pass on deterministic and adversarial contract tests"). It states
eight principles but no threat model: no adversary capabilities, no discussion of who can write to
the episode stream, no analysis of the memory-poisoning attack it claims resistance to beyond one
sentence.

Given that "poisoning resistance" and "zero cross-workspace leakage" are gated, this chapter needs
a threat model with named adversaries and the specific adversarial tests that operationalise each
principle. Chapter 14 hints those tests exist; connect them.

## B8. Chapters 12 and 14 overlap — MINOR

Chapter 12 carries "Current status" for Phases 0–2; Chapter 14 restates the same status in more
detail. Keep the forward-looking plan in 12 and the as-built status in 14, with no status text in
12 — or merge them.

---

# Part C — Mechanical defects

These are unambiguous and mostly scriptable. Together they are the difference between "working
draft" and "submittable."

| # | Issue | Location | Severity |
|---|---|---|---|
| C1 | **No bibliography management at all.** `_quarto.yml` has no `bibliography:` or `csl:` field; `references.qmd` is a hand-maintained list; every in-text citation is hardcoded plain text. No citation is a link, nothing is checked, and drift is inevitable. | repo-wide | **critical** |
| C2 | **All mathematics renders as broken plain text.** `e_i=(id_i,t_event_i,…)`, `c_k^(v)=(q_k,s_k,…)`, `R(c,q)=w1 S1+w2 S2+…`, `confidence(c)=1/(1+exp(-z_c))`, `I(q,t,p,b)=(C*,E*,A*,U*,X*,L*)`. Subscripts render literally; the tuples are unreadable. Also inconsistent within a single chapter (`yi` and `y_i` in the same sentence in Ch 4). | Ch 2, 4, 5 | **critical** |
| C3 | **Hard-wrap artifacts split sentences mid-flow into separate paragraphs.** e.g. Ch 3: "…revised by a designer that examines hard cases (H. Zhang et al.\n\n2026)." Ch 7: "(He et al.\n\n2026)". `references.qmd` has ~8 entries split mid-title. Looks like a column-limit script ran over the source. | Ch 3, 5, 7, 10, references | major |
| C4 | **Blank lines split bullet lists into two lists.** Ch 2 (between "Revisable" and "Actionable"), Ch 5 (after the first scheduling bullet). Renders as two separate lists in HTML and PDF. | Ch 2, 5 | major |
| C5 | **Pseudocode is not in a code block.** Ch 5's concept-proposal procedure runs together as prose: "for each reflection cluster R: evidence = union(…) counter = retrieve…". Unreadable. | Ch 5 | major |
| C6 | **Leftover text from an earlier draft.** Ch 13 line 7 begins "**L** is not primarily a chatbot…" — a stale rename, should be ELL. Ch 13 line 25: "The **v0.1 paper** distinguishes episodes…" — this is v0.6. | Ch 13 | major |
| C7 | **No cross-reference machinery.** Seven textual "Section 7 / Section 11" references that should be `@sec-` cross-refs; zero figure labels, so no figure is numbered or referenceable, and no figure is ever referred to from body text. `crossref` is unconfigured. | Ch 2, 7, 12, 13, 14 | major |
| C8 | **Orphan reference.** Zhong et al. 2024 (MemoryBank) is in `references.qmd` and cited nowhere in the text. Either cite it in Ch 3 (it belongs in the production-memory family) or remove it. | references | moderate |
| C9 | **Citation name inconsistency.** Ch 9 cites "(Zhang et al. 2026)"; Ch 3 cites the same paper as "(J. Zhang et al. 2026)". There are two distinct Zhang 2026 references (J. Zhang, *Beyond Similarity*; H. Zhang, *MemSkill*), so the Ch 9 form is ambiguous. | Ch 9 | moderate |
| C10 | **System names in the positioning table do not match the cited titles.** The table lists "AgeMem, AutoMEM, MemCon (Y. Yu et al. 2026; Chen et al. 2026; Jiang et al. 2026)", but the Chen 2026 reference is titled *Exploring Cross-Scenario Generality…* and Jiang 2026 is *Memory as a Controlled Process*. Neither title contains the system name used. Add the system name to the reference entry or drop the alias. Also: Chen et al. 2026 is used in Ch 3 both for the flat-file-baseline finding and as "AutoMEM" — clarify whether these are the same artifact. | Ch 3 | moderate |
| C11 | **Duplicate figures.** `ell-overview` appears in `index.qmd` and again in Ch 4; `governed-commit` appears with an identical caption in Ch 6 and Ch 13. | index, Ch 4, 6, 13 | moderate |
| C12 | **Unused asset.** `chapters/assets/diagrams/ell-lifecycle-context.svg` is referenced nowhere. | assets | minor |
| C13 | **Chapter 11's filename no longer matches its title.** File is `11-expected-outcomes-and-falsifiability.qmd`; heading is "Definition of Success and Falsifiability". | Ch 11 | minor |
| C14 | **No archival metadata.** Ch 8 says machine-readable citation metadata "should" be included in a future release; there is no `CITATION.cff`, no ORCID, no DOI/Zenodo deposit. Phase 0's exit criterion requires an immutable tag, so this is on the critical path. | repo | moderate |
| C15 | **PDF/HTML config gaps.** No `number-sections` for HTML (so the "Section N" references have nothing to point at in the web edition), no `crossref` block, no `bibliography`/`csl`. | `_quarto.yml` | moderate |

---

# Recommended sequence

**Round 1 — unblock the preregistration** (these change what the study *is*, so they come first)

1. A1: power the non-inferiority gate; resize N (A3) on a defensible discordance estimate (A4).
2. A2: declare a conjunctive-power target, or split confirmatory from release-blocking gates.
3. A5: separate the Chapter 11 table into comparative gates and absolute invariants.
4. A6 + A7: add oracle-concept condition and randomised packet inclusion to Chapter 7.
5. A8: write out the confidence and relevance functions completely.
6. Re-freeze `research-contract-v0.6.json` — or, more honestly, cut **v0.7** and describe v0.6 as
   not having been frozen. A contract that changes after being called frozen is worse than a
   contract that was never called frozen.

**Round 2 — mechanical cleanup** (one focused day; C1 and C2 are the two that matter)

7. C1: move to `references.bib` + `@citekeys` + a CSL file. This also fixes C8, C9, C10 by making
   them detectable.
8. C2: convert all mathematics to LaTeX display math; add a notation table.
9. C3, C4, C5: run a re-wrap and lint pass over every `.qmd`. Add a CI check so it does not recur.
10. C6, C7, C11–C15: labels, cross-refs, stale text, config, `CITATION.cff`.

**Round 3 — strengthen the argument**

11. B3: the capability matrix. Do this one even if you do nothing else in Round 3.
12. B4: the worked end-to-end trace.
13. B1, B2: cut redundancy; demote Chapter 13 to an appendix. Target ~13k words.
14. B5, B6, B7: unify packet naming, tighten the abstract, expand the threat model.
15. A12: the RQ → hypothesis → metric → gate → phase table.

---

## What is already good, and should not be touched

- The claim hierarchy in Chapter 2 (RQ3 primary, RQ1 as its safety guardrail) is exactly right and
  rare in this literature.
- Chapter 10's self-criticism, particularly the representational-favouritism and causal-attribution
  points, is stronger than most external review would produce.
- "Benchmark before ELL" as Phase 1, with a stop condition if the benchmark cannot distinguish
  known-good from deliberately broken policies, is excellent research hygiene.
- The two-cost-view accounting rule — "a system is not credited with efficiency by moving work into
  an unreported background process" — closes a loophole most memory papers exploit.
- Separating confidence from eloquence, and refusing LLM self-reported certainty, is a real
  contribution independent of whether the transfer result holds.
- Chapter 14 explicitly refusing to treat passing unit tests as evidence for H1–H6 is the correct
  posture and should be preserved verbatim.
