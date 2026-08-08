

--- Page 1 ---
From Episodes to Revisable Concepts
The Experience Learning Layer for Evidence-Grounded Learning 
in Language Agents
Danny Ruchtie
Living working draft v0.2 - 8 August 2026
Revision note. Version 0.2 retains the preregistered research proposal from v0.1 and adds the product architecture, governed memory model, provider boundaries, and verified Phase 0 implementation status established on 8 August 2026. The archived v0.1 PDF remains available for comparison.
OPEN RESEARCH SPECIFICATION  ·  EXPERIMENTAL PROTOCOL
Research status. This document is a working architecture paper and preregistered evaluation plan. It defines the 
proposed system, hypotheses, data model, implementation contract, and experiments. It does not report empirical 
results. Results will be added only after the open implementation and evaluation harness can reproduce them.
Abstract
Large language model agents can store and retrieve previous interactions, yet retrieval alone does not establish that 
an agent has learned from experience. Learning requires a system to identify patterns across episodes, distinguish 
observations from hypotheses, form reusable concepts, apply those concepts in new situations, and revise them 
when later evidence disagrees. Recent agent-memory research has introduced reflection, experience-derived 
insights, workflow induction, dynamic memory graphs, semantic and procedural memory, schema induction, and 
temporally grounded updates. The remaining challenge is therefore not simply to add another memory store, but to 
make the transition from experience to general knowledge explicit, inspectable, revisable, and directly measurable.
This paper proposes the Experience Learning Layer (ELL), an open, model-independent architecture positioned 
between an agent’s experience history and its decision process. ELL preserves raw episodes in an append-only 
store, creates typed associations between them, represents reflections as provisional interpretations, and promotes 
compatible reflections into versioned concepts. Each concept records its scope, supporting evidence, 
counterevidence, confidence, temporal validity, lineage, and observed utility. Concepts can be corroborated, 
contested, revised, superseded, or retired without erasing their evidential history.
The paper contributes a typed architecture, a concept-lifecycle protocol, an evidence ledger, an experimental 
benchmark for controlled concept induction, and a reproducibility plan based on openly licensed code and open-
weight models. The central hypothesis is that separating reflection from concept consolidation, while preserving 
support and counterevidence, will improve transfer to structurally similar situations and reduce unsupported 
generalisation compared with episode-only retrieval or direct summarisation. The proposal is deliberately 
falsifiable: concept correctness, evidence coverage, revision behaviour, transfer, downstream task success, 
calibration, and cost are all measured independently.
Keywords: agent memory; experiential learning; reflection; concept formation; semantic memory; continual 
learning; provenance; language agents; open source
1. Introduction
A language agent can remember an earlier event without learning anything general from it. A retrieval system 
may surface five examples of the same failure, yet the agent may still repeat that failure because the episodes 
have never been converted into a reusable and appropriately scoped principle. This distinction matters as 
agents move from single-turn assistance toward persistent collaboration, long-running tasks, and multi-session 
interaction.
The first generation of agent-memory systems established that external memory could improve continuity 
beyond a model’s context window. Generative Agents stored observations, ranked them for retrieval, and 
periodically synthesised higher-level reflections that influenced later plans (Park et al. 2023). Reflexion used 
textual feedback about prior attempts as a non-parametric learning signal (Shinn et al. 2023). ExpeL extracted 
natural-language insights from collections of task experiences and reused both insights and successful 

--- Page 2 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
2
trajectories at inference time (Zhao et al. 2024). MemGPT approached the problem as virtual context 
management, allowing an agent to move information between limited working context and external storage 
(Packer et al. 2023). CoALA organised these developments within a broader cognitive architecture containing 
working, episodic, semantic, and procedural memory (Sumers et al. 2024).
Subsequent systems have increasingly abstracted experience rather than merely retrieving it. Voyager 
accumulated reusable executable skills (G. Wang et al. 2023). Agent Workflow Memory induced recurring 
action routines from prior trajectories (Z. Z. Wang et al. 2025). A-MEM dynamically linked and revised 
memory notes as new information arrived (Xu et al. 2025). Reflective Memory Management used prospective 
and retrospective reflection to improve memory granularity and retrieval (Z. Tan et al. 2025). Temporal 
Semantic Memory consolidated temporally related events into durative representations (Su et al. 2026). More 
recent architectures explicitly construct schemas, concepts, semantic knowledge, or procedural knowledge 
from episodes, including DCPM, GAAMA, and PlugMem (Fei et al. 2026; Paul, Sharma, and Sareen 2026; 
Yang et al. 2026).
This rapid progress changes the research question. It is no longer defensible to claim that transforming 
episodes into abstractions is itself novel. The more precise question is:
How should an agent maintain a transparent and revisable chain from raw experience, through 
provisional interpretation, to general concepts whose evidential support and behavioural usefulness 
can be tested?
ELL addresses this question by separating four objects that are often collapsed into one textual memory:
1. An episode records what occurred in a specific context.
2. A reflection is a provisional interpretation of one or more episodes.
3. A concept is a reusable proposition or strategy supported by multiple reflections and episodes.
4. An application outcome records whether using a concept helped in a later situation.
The separation is important because a plausible explanation is not automatically reliable knowledge. Suppose a 
project proposal is rejected after stakeholders were consulted late. A reflection may state that late stakeholder 
involvement caused the rejection. That is a useful hypothesis, but a single episode does not justify a universal 
rule. A concept should only be promoted after corroborating cases, explicit checks for counterexamples, and a 
scope statement such as “cross-functional initiatives with external implementation dependencies.” New 
evidence may later narrow, challenge, or replace it.
ELL treats every concept as a versioned claim rather than a timeless fact. The system retains the episodes that 
support it, episodes that contradict it, the contexts in which it has been applied, and the outcomes of those 
applications. This makes concept formation inspectable and enables evaluation at the level where learning is 
claimed to occur.
The architecture is inspired by, but does not attempt to reproduce, human memory. Tulving’s distinction 
between episodic and semantic memory motivates the separation between event-specific records and general 
knowledge (Tulving 1972). Complementary Learning Systems theory motivates a fast episodic path and a 
slower consolidation path that integrates common structure across experiences (McClelland, McNaughton, and 
O’Reilly 1995; Kumaran, Hassabis, and McClelland 2016). Bartlett’s account of reconstructive remembering 
provides a warning as much as an inspiration: abstraction can impose existing schemas on ambiguous 
experience and thereby distort it (Bartlett 1932). For this reason, ELL preserves provenance, counterevidence, 
and reversible revisions.
1.1 Scope
ELL is an external learning layer. It does not update the parameters of the underlying language model. It 
does not prescribe how raw activity is captured from calendars, files, screens, sensors, or chat applications. It 
starts after an application has produced a canonical stream of consented experience records. It is designed to 
support conversation histories, task trajectories, product-work records, and other event streams through a 
shared schema.

--- Page 3 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
3
The initial research scope is deliberately narrower than a complete personal-intelligence system. It focuses on:
• association between episodes;
• reflection over individual and grouped episodes;
• concept formation and consolidation;
• application of concepts to later decisions;
• revision after new evidence and outcomes;
• direct evaluation of concept quality and transfer.
Perception, multimodal capture, large-scale identity resolution, and parametric fine-tuning are outside the first 
paper.
1.2 Contributions
This working paper specifies five intended contributions.
A typed experience-to-concept architecture. It defines distinct schemas and operations for episodes, 
associations, reflections, concepts, evidence links, applications, and outcomes.
An evidence-grounded concept lifecycle. Concepts move through explicit states—proposed, corroborated, 
contested, revised, superseded, and retired—while retaining lineage and provenance.
A separation between confidence and eloquence. Concept confidence is computed from observable 
evidence, contradiction, diversity, and outcome history rather than accepted directly from an LLM’s self-
reported certainty.
A direct evaluation protocol. In addition to downstream task performance, the evaluation measures concept 
correctness, evidence precision and recall, scope accuracy, contradiction handling, revision latency, 
calibration, transfer, and cost.
An open reference implementation. Versioned releases will include code, schemas, prompts, experiment 
configurations, synthetic data generators, evaluation scripts, and paper sources under permissive licences, with 
reproducibility runs using open-weight models.
2. Problem Definition
2.1 Experience learning
Let an agent encounter an ordered experience stream
E={e1 ,e2 ,…,en}.
Each episode ei contains a time-bounded record of context, observation, action, outcome, source, and 
metadata. Given this stream, an experience-learning system should produce a set of concepts C that improve 
decisions on future situations while remaining grounded in the episodes from which they were induced.
The goal is not to compress the entire history into a shorter text. Compression can preserve frequent 
information while losing exceptions, causal uncertainty, temporal change, and source identity. The desired 
output is a set of claims or strategies with explicit conditions and evidence.
A concept is useful only if it satisfies several properties:
• Grounded: its support can be traced to specific episodes and reflections.
• General: it applies beyond a single remembered case.
• Scoped: it states where it is expected to apply and where it may not.
• Revisable: contradictory evidence can change its status or content.

--- Page 4 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
4
• Actionable: it can affect a later response, plan, or decision.
• Measurable: its correctness and utility can be evaluated independently.
2.2 Failure modes addressed
ELL is designed around seven common failure modes.
Episode replay without abstraction. Relevant cases are retrieved, but no reusable principle is formed.
Premature generalisation. A single salient episode becomes a broad rule.
Self-confirming reflection. Once a reflection is stored, later retrieval favours evidence that agrees with it.
Context collapse. A concept loses the conditions under which it was valid.
Temporal staleness. New evidence changes what is true, but the old concept continues to guide behaviour.
Provenance loss. A generated statement can no longer be connected to the experience that justified it.
Behavioural ambiguity. A system claims to have learned because it stored a summary, without showing 
improved transfer or decision quality.
2.3 Research questions
The first empirical study will answer four questions.
RQ1 — Separation. Does representing reflections as provisional objects before concept consolidation reduce 
unsupported generalisation compared with direct episode-to-rule summarisation?
RQ2 — Revision. Do explicit counterevidence, temporal validity, and versioned lifecycle states improve 
adaptation when the underlying pattern changes?
RQ3 — Transfer. Do consolidated concepts improve performance on new situations that share latent structure 
but differ in wording and surface details?
RQ4 — Efficiency. Can compact concepts plus selected source episodes match or improve downstream 
performance while using less retrieval context than episode-only methods?
2.4 Hypotheses
H1. ELL will produce higher concept-scope accuracy and lower overgeneralisation than a direct insight-
extraction baseline.
H2. ELL will revise or contest invalid concepts more quickly after contradictory evidence than append-only 
reflection or rolling-summary baselines.
H3. ELL will yield a positive transfer gain on held-out tasks whose latent rule is represented in prior 
experiences, even when lexical similarity to those experiences is low.
H4. Retrieving concepts together with a small number of supporting episodes will reduce median input tokens 
per decision without reducing task success.
These hypotheses are falsified if the confidence intervals include no practically meaningful improvement, if 
concept-level gains fail to translate into behaviour, or if the added architecture costs more than the retrieval it 
replaces without delivering measurable benefits.

--- Page 5 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
5
3. Related Work and Positioning
3.1 Persistent context and episodic retrieval
Long-term agent memory initially focused on maintaining continuity beyond a finite context window. 
MemoryBank stored and updated user-related memories for sustained interaction (Zhong et al. 2024), while 
MemGPT introduced a virtual-memory analogy in which an agent manages different context tiers (Packer et 
al. 2023). Zep later represented evolving information in a temporal knowledge graph (Rasmussen et al. 2025). 
These systems demonstrate that long-running interaction requires explicit write, update, and retrieval 
mechanisms rather than a single ever-growing prompt.
Benchmarks have exposed the limits of retrieval-centric designs. LoCoMo evaluates question answering, 
summarisation, and dialogue generation over long multi-session conversations (Maharana et al. 2024). 
LongMemEval tests information extraction, cross-session reasoning, temporal reasoning, knowledge updates, 
and abstention (Wu et al. 2025). These tasks are central to persistent memory, but they primarily evaluate 
whether a system can recover or reason over stored information. They do not fully determine whether a general 
concept was correctly induced.
3.2 Reflection and non-parametric learning
Generative Agents introduced periodic reflection over accumulated observations, producing higher-level 
statements that could themselves be retrieved (Park et al. 2023). Reflexion showed that verbal feedback stored 
in episodic memory can improve repeated task attempts without weight updates (Shinn et al. 2023). ExpeL 
extended this idea by extracting insights across training experiences and transferring them to test tasks (Zhao et 
al. 2024). Reflective Memory Management used forward-looking summarisation and backward-looking 
evidence-based retrieval refinement (Z. Tan et al. 2025).
These systems establish reflection as a useful learning operator. ELL adopts that operator but makes a stricter 
distinction: a reflection is a candidate interpretation, not yet a trusted concept. This distinction enables explicit 
evidence thresholds, counterevidence checks, and lifecycle transitions.
3.3 Semantic, procedural, and graph-based abstraction
A second line of work converts experience into structured knowledge or reusable procedures. Voyager stores 
executable skills; Agent Workflow Memory induces reusable task routines; and A-MEM dynamically 
organises memory notes through contextual attributes and links (G. Wang et al. 2023; Z. Z. Wang et al. 2025; 
Xu et al. 2025). Temporal Semantic Memory aggregates temporally continuous evidence into durative user 
representations (Su et al. 2026).
The closest recent systems move explicitly from episodes to abstractions. DCPM separates fast fact updates 
from slower induction of schemas, intentions, and cross-domain patterns, with evidence links to supporting 
facts (Fei et al. 2026). GAAMA constructs a typed graph with episode, fact, reflection, and concept nodes 
(Paul, Sharma, and Sareen 2026). PlugMem derives semantic and procedural knowledge graphs from 
standardised episodic traces and maintains provenance to source episodes (Yang et al. 2026).
ELL is complementary to these architectures rather than a claim to precede them. Its intended distinction is the 
epistemic lifecycle of a concept. The core research object is not only a graph node or summary, but a claim 
with:
• separate supporting and contradicting evidence;
• an explicit applicability scope;
• a confidence calculation based on observable signals;
• temporal validity and version lineage;
• recorded downstream applications and outcomes;
• direct concept-level evaluation.

--- Page 6 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
6
The implementation can use a graph, relational database, vector index, or a combination. The contribution is 
the contract and lifecycle, not a requirement for one storage technology.
3.4 Evaluation of agent memory
MemBench broadens evaluation to factual and reflective memory under different interaction roles, measuring 
effectiveness, efficiency, and capacity (H. Tan et al. 2025). MemoryArena further couples memory with later 
action in multi-session agent-environment loops (He et al. 2026). These directions are important because 
successful retrieval does not guarantee useful behaviour.
ELL adds a controlled concept-induction benchmark in which the latent patterns, exceptions, supporting 
episodes, and change points are known. Existing benchmarks are retained for ecological validity, while the 
controlled benchmark isolates whether a system formed the right concept for the right reasons.
3.5 Cognitive inspiration and its limits
The episodic-semantic distinction and complementary learning systems provide useful engineering metaphors 
(Tulving 1972; McClelland, McNaughton, and O’Reilly 1995; Kumaran, Hassabis, and McClelland 2016). 
They suggest preserving specific experiences while separately integrating common structure. However, ELL is 
not a neuroscientific model. LLM-generated natural-language concepts, database records, and scheduled 
consolidation jobs are functional approximations. Biological terminology is used to clarify roles, not to claim 
mechanistic equivalence.
4. Experience Learning Layer Architecture
Figure 1. Proposed ELL architecture. The append-only episode store and evidence ledger preserve source history while reflections 
and concepts remain revisable.
ELL is organised as a write–associate–reflect–consolidate–apply–evaluate loop. Each component exposes a 
narrow interface so that models, stores, and retrieval methods can be replaced independently.

--- Page 7 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
7
4.1 Canonical episode store
The input is a canonical episode rather than an application-specific chat message. An episode is represented as
ei=( ιi,ti,^ti,xi,oi,ai,yi,si,pi) ,
where ιi is the episode identifier, ti and ^ti are event and observation time, xi is context, oi is an observation, ai 
is an action, yi is an outcome, si is source metadata, and pi contains privacy and access-control metadata. The 
two timestamps allow delayed reports and later corrections to be represented.
The raw episode store is append-only. Corrections create new records linked by relations such as corrects, 
supersedes, or retracts. This preserves an audit trail and prevents an abstraction process from silently 
rewriting its own evidence.
4.2 Association layer
The association layer creates typed links between episodes. Initial relation types are:
• semantic similarity;
• shared entities or participants;
• temporal proximity or sequence;
• shared goal or task;
• shared action pattern;
• similar outcome;
• candidate causal relation;
• contradiction or correction.
Only some edges are objective. Temporal sequence and shared identifiers can be deterministic; causal and 
contradiction edges may be model-generated hypotheses. Every edge therefore records its method, score, 
model or rule version, and source evidence.
The layer supports both local neighbourhood retrieval and clustering. Reflection should not operate only on the 
nearest embeddings because lexically distant episodes may share a goal, failure pattern, or outcome. Hybrid 
candidate generation combines semantic, structural, temporal, and outcome-based signals.
4.3 Reflection Engine
A reflection is a provisional interpretation:
rj=( hj,tj,sj,pj,nj,uj,zj) .
Here hj is a claim or question, tj is reflection type, sj is scope, pj and nj are supporting and counterevidence 
episode sets, uj is uncertainty metadata, and zj is review status.
Reflection types include:
• observation or recurring pattern;
• causal hypothesis;
• strategy or procedural lesson;
• preference hypothesis;
• anomaly or exception;
• unresolved question;
• candidate correction to an existing concept.

--- Page 8 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
8
The Reflection Engine is triggered by configurable events: a cluster reaching a minimum size, a repeated 
failure, a surprising outcome, new contradiction, elapsed time, or an explicit request. It produces structured 
output and is followed by an evidence-validation pass. Reflections may remain unverified, be marked 
supported, or be rejected before they reach the Concept Engine.
4.4 Concept Engine
A concept is a reusable, versioned proposition or strategy:
ck
( v)=( qk,sk,ak,ik,pk,nk,gk,tk,v,zk) .
Here qk is the proposition, sk is scope, ak is a set of applicability conditions, ik is the expected implication or 
recommended behaviour, pk and nk are supporting and counterevidence sets, gk is confidence, tk is temporal 
validity, v is version, and zk is lifecycle state.
Concept types include descriptive patterns, user preferences, causal hypotheses, strategies, constraints, and 
procedural rules. The first implementation focuses on textual concepts, but the schema permits executable 
procedures or references to code artefacts.
The Concept Engine performs five operations:
1. Propose: create a candidate concept from compatible reflections.
2. Merge: combine concepts that express the same claim and scope.
3. Split: separate an over-broad concept when evidence supports distinct conditions.
4. Revise: create a new version with changed claim, scope, validity, or confidence.
5. Retire or supersede: stop active use while preserving lineage.
Promotion requires evidence from more than one episode unless a domain-specific policy explicitly permits 
single-source facts. Evidence diversity is measured across time, source, participant, task, and surface form to 
reduce duplicate episodes being mistaken for independent support.
4.5 Concept registry and evidence ledger
The concept registry contains the current active version of each concept and its full version chain. The 
evidence ledger is append-only and records:
• which episodes supported or contradicted a reflection;
• which reflections contributed to a concept version;
• which model, prompt, rule, or human action produced a change;
• which concepts were retrieved for a decision;
• what action was taken and what outcome followed;
• deletions, access changes, and invalidations.
This ledger supports explanation and reproducibility. A user or evaluator should be able to ask: “Why does the 
system believe this?”, “What evidence disagrees?”, “When did this change?”, and “Did using it help?”
4.6 Learning retrieval and application
At decision time, the retrieval service selects a mixture of concepts and source episodes. Concepts provide 
compact general guidance; episodes provide specificity, exception handling, and verification. The retrieval 
policy must be able to return either type independently.
A concept relevance score can initially be expressed as
R( c,q)=w1 S1+w2 S2+w3 S3+w4 S4+w5 γc−w6 S6 ,

--- Page 9 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
9
where S1 through S4 represent semantic relevance, scope match, temporal validity, and observed utility; γc is 
concept confidence; and S6 is active contradiction. This formula is a design heuristic, not a validated scientific 
result. Weights will be tuned only on development data and frozen before test evaluation.
The retrieved package includes the concept statement, scope, confidence, current state, relevant support, 
relevant counterevidence, and source links. Applications can require a minimum confidence or allow contested 
concepts to be shown as uncertainty rather than instructions.
4.7 Outcome loop
Every use of a concept creates an application record:
am=( xm,Cm,Em,dm,ym,um) .
Here xm is the task context, Cm and Em are the concepts and episodes used, dm is the decision, ym is the 
observed outcome, and um is utility. Outcome feedback can come from task reward, user correction, validator 
output, or later observed consequences. The system must not automatically treat every positive result as proof 
of causality; outcomes are recorded as validation signals with their own reliability. Repeated success can 
strengthen a concept, while failure can add counterevidence, narrow scope, or trigger revision.
4.8 Lifecycle
Figure 2. Concept lifecycle. Revisions create new versions rather than overwriting evidential history.
The lifecycle is intentionally reversible. Corroborated does not mean permanently true. Contested concepts 
may still be retrieved when their uncertainty is relevant. Superseded concepts remain available for historical 
questions, while retired concepts are excluded from ordinary guidance.
5. Proposed Algorithms
5.1 Reflection scheduling
Running reflection after every episode would be expensive and may create redundant interpretations. ELL 
therefore uses event-based scheduling. An episode or cluster enters the reflection queue when one or more 
conditions are met:
• the cluster contains at least n distinct episodes;

--- Page 10 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
10
• a failure or unusually high reward occurs;
• a new episode contradicts an active concept;
• association novelty exceeds a threshold;
• the concept has not been reviewed within a time window;
• a user or agent explicitly requests reflection.
The scheduler records why a job was triggered. This enables later analysis of whether a scheduling policy 
created useful concepts or unnecessary model calls.
5.2 Reflection generation and critique
The Reflection Engine receives a bounded evidence packet: selected episodes, existing nearby reflections, 
relevant active concepts, and an instruction to produce typed hypotheses. The generator must output structured 
fields rather than a free-form essay.
A separate validation pass performs four checks:
1. Entailment: Does each cited episode actually support the claim attributed to it?
2. Contradiction: Are there nearby episodes that disagree?
3. Scope: Is the claim broader than its evidence?
4. Novelty: Is the reflection meaningfully different from existing reflections or concepts?
The validator can be an independent model, a deterministic rule, a human reviewer, or a combination. Using a 
separate model call does not guarantee independence, so experiments will include same-model and cross-
model validation conditions.
5.3 Concept proposal
Reflections are grouped by semantic compatibility and scope overlap. A proposed concept requires:
• at least m compatible reflections;
• at least d distinct supporting episodes;
• minimum evidence diversity;
• no unresolved high-confidence contradiction;
• an explicit scope and exception list;
• a concise proposition and expected implication.
The default policy will require support from at least three episodes across at least two distinct contexts. This is 
a configurable research parameter rather than a universal rule.
A simplified proposal procedure is:
for each reflection cluster R:
    evidence = union(supporting episodes in R)
    counter = retrieve plausible counterevidence
    candidate = generate_concept(R, evidence, counter)
    checks = validate(candidate, evidence, counter)
    if checks pass promotion policy:
        register(candidate, state="proposed")
5.4 Evidence-weighted confidence
LLMs are not assumed to be calibrated judges of their own abstractions. ELL computes an operational 
confidence score from external features:

--- Page 11 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
11
γ( c)= 1
1+e−zc
,
where zc is a weighted score that increases with supporting evidence, evidence diversity, and observed 
application utility, and decreases with counterevidence, age without revalidation, and validator disagreement.
The formula is deliberately transparent and will be calibrated on held-out development data. A simpler 
Bayesian or rule-based alternative will be included as a baseline. Confidence is never used to hide 
counterevidence; the raw counts and links remain visible.
5.5 Revision and temporal validity
When new evidence conflicts with a concept, the system chooses among four responses:
• add exception: the core claim remains valid but has a narrower boundary;
• narrow scope: the concept was over-generalised;
• change validity interval: the pattern was true during one period but is no longer current;
• replace claim: a new concept version better explains the evidence.
Revision produces a new immutable version linked by revises or supersedes. The old version retains its 
former validity interval and applications. This design supports historical reasoning and avoids treating changed 
preferences or conditions as contradictions that must erase the past.
5.6 Merge and split
Duplicate concepts increase retrieval noise, while over-broad concepts hide meaningful exceptions. Merge 
candidates are identified using proposition similarity, overlapping evidence, compatible scope, and similar 
implications. Split candidates are triggered when counterevidence clusters around a coherent condition or 
when application outcomes differ significantly by context.
Both operations require a lineage record. A merge creates a new concept that references all parents. A split 
creates child concepts whose evidence partitions are explicit. Automated operations above a risk threshold can 
require human approval.
5.7 Retrieval with evidence restoration
Concept retrieval follows two stages. The first stage selects concepts by semantic, structural, temporal, and 
utility signals. The second restores a small, query-specific set of source episodes. This prevents a compact 
concept from becoming an ungrounded instruction.
The retrieval budget is fixed in tokens or characters so that systems are compared under equal context cost. 
This avoids rewarding a method merely for retrieving far more text. Results report both task utility and 
memory information density.
5.8 Deletion and invalidation
A user must be able to delete source data. Deletion cannot stop at the episode store because derived concepts 
may still encode the removed information. ELL maintains derivation links so a deletion request can:
1. remove or tombstone the source episode according to policy;
2. remove it from support and counterevidence sets;
3. recompute affected confidence values;
4. contest, revise, or retire concepts that no longer meet support thresholds;
5. record the deletion cascade without retaining prohibited content.

--- Page 12 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
12
This is both a privacy requirement and a scientific requirement: provenance is incomplete if derived claims 
cannot be invalidated when their evidence disappears.
6. Data Model and Public Interfaces
6.1 Core entities
Entity Purpose Required fields
Episode Immutable record of a bounded 
experience
ID, event time, observed time, 
context, observation, action, outcome, 
source, access metadata
Association Typed relation between episodes or 
knowledge objects
source ID, target ID, relation type, 
score, method, provenance
Reflection Provisional interpretation or question statement, type, scope, support, 
counterevidence, uncertainty, status
Concept Reusable versioned knowledge object
proposition, scope, conditions, 
implication, support, counterevidence, 
confidence, validity, version, lifecycle 
state
Application Record of concept use task, retrieved concepts, retrieved 
episodes, decision, timestamp
Outcome Evidence about application result reward or judgement, source, 
reliability, delay, linked application
AuditEvent Immutable record of system change actor, operation, object, prior version, 
new version, method, timestamp
6.2 Concept states
• proposed: generated and valid enough to test, but not yet strongly supported;
• corroborated: meets evidence and validation thresholds;
• contested: important unresolved counterevidence exists;
• revised: a new immutable version has been created in response to changed evidence and is awaiting 
or recording validation;
• superseded: replaced by a newer or more precise concept;
• retired: no longer eligible for ordinary retrieval;
• deleted: content removed under deletion policy, with only non-sensitive structural audit metadata 
retained where legally permitted.
A revision never overwrites its parent. A revised version can later become corroborated, contested, superseded, 
retired, or deleted while its lineage remains traceable.
6.3 API contract
The reference implementation exposes the following model-independent operations:
record_episode(episode) -> EpisodeID
associate(episode_id, policy) -> list[Association]
run_reflection(scope, trigger) -> list[Reflection]
reconcile_concepts(reflection_ids) -> list[ConceptVersion]
retrieve_learning(query, context, budget) -> LearningPacket
record_application(packet, decision) -> ApplicationID
record_outcome(application_id, outcome) -> list[ConceptUpdate]
explain_concept(concept_id, version=None) -> EvidenceReport
delete_subject_data(subject_id, policy) -> DeletionReport

--- Page 13 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
13
LearningPacket is the central read object. It contains concepts, relevant evidence, conflicts, and budget 
accounting. It never contains only a naked concept statement.
6.4 Storage independence
The core schema is storage-neutral. The starter implementation uses an in-memory store; a SQLite adapter is 
planned as the first persistent baseline. Production adapters may add PostgreSQL, a vector index, or a graph 
database. Storage choices are evaluated by correctness, write cost, query latency, deletion support, and 
operational simplicity rather than by architectural fashion.
The same principle applies to model providers. The engine depends on a structured-generation interface, not a 
vendor SDK. Reproducibility experiments use open-weight models, while optional adapters may support 
hosted models for comparison.
7. Experimental Design
7.1 Study status
The evaluation is preregistered in this paper before results are collected. All thresholds, prompts, model 
versions, random seeds, exclusions, and statistical tests will be committed before the sealed test sets are run. 
Any later changes will be reported as deviations rather than silently folded into the method.
7.2 Evaluation stages
Stage A: controlled latent-pattern streams
The project will release a synthetic benchmark in which each experience stream is generated from known 
latent concepts. A stream contains:
• recurring contextual rules;
• paraphrased surface forms;
• irrelevant but semantically similar episodes;
• exceptions with explicit conditions;
• contradictory observations;
• temporal change points;
• delayed outcomes;
• duplicated or correlated evidence.
Example latent concept:
When a task depends on another team and the owner is not involved before commitment, delivery risk 
increases; the pattern does not apply to independently executable tasks.
The generator creates episodes that support, contradict, or fall outside the concept’s scope. The benchmark 
therefore has gold labels for the concept, its conditions, its evidence, counterevidence, and validity interval.
Three stream lengths are planned: 50, 200, and 1,000 episodes. Difficulty increases through noise, lexical 
distance, exceptions, and concept drift. A sealed test generator seed prevents manual prompt tuning against the 
exact cases.
Stage B: long-term conversational memory
LongMemEval and LoCoMo will test whether ELL remains competitive on factual extraction, cross-session 
reasoning, temporal reasoning, updates, abstention, and long-range dialogue understanding (Wu et al. 2025; 

--- Page 14 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
14
Maharana et al. 2024). MemBench will add reflective-memory and efficiency measures where licensing and 
harness compatibility permit (H. Tan et al. 2025).
ELL is not expected to dominate span-recall tasks solely because it forms concepts. These benchmarks test 
whether the abstraction layer preserves ordinary memory performance and whether concept retrieval helps 
multi-session inference.
Stage C: memory-dependent action
MemoryArena will test whether information learned in earlier sessions improves later task execution (He et al. 
2026). A smaller open environment may be added for rapid iteration, but MemoryArena is the target action 
benchmark because it explicitly couples memory, agent decisions, and environment outcomes.
7.3 Baselines
At minimum, all experiments include:
1. no persistent memory;
2. full or maximum available context;
3. vector retrieval over raw episodes;
4. rolling summary memory;
5. episode retrieval plus direct insight extraction;
6. ELL without concept consolidation;
7. full ELL.
Where reproducible implementations and compatible licences are available, A-MEM, Reflective Memory 
Management, GAAMA, and PlugMem will be evaluated using their released code or carefully documented 
reimplementations (Xu et al. 2025; Z. Tan et al. 2025; Paul, Sharma, and Sareen 2026; Yang et al. 2026). A 
method will not be included under another system’s name if key behaviour cannot be reproduced.
7.4 Model conditions
The main reproducibility track uses at least two openly licensed instruction-tuned models from different model 
families and two capacity bands. Model names are recorded only when the experiment is frozen, because 
available open models change rapidly. All generation settings, quantisation, serving software, prompts, and 
hardware are logged.
A hosted-model comparison may be reported separately, but the paper’s core claims must remain reproducible 
without proprietary APIs.
7.5 Metrics
Downstream metrics
• task success or benchmark accuracy;
• answer faithfulness to retrieved evidence;
• transfer gain over the episode-only baseline;
• abstention quality;
• action efficiency, including steps to completion.
Concept metrics
Concept correctness. Does the induced proposition match the gold latent pattern or human judgement?
Evidence precision. What proportion of cited support actually supports the concept?

--- Page 15 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
15
Evidence recall. What proportion of relevant support was linked?
Counterevidence recall. Did the system find important exceptions and contradictions?
Scope accuracy. Does the concept apply to the right contexts without over-generalising?
Revision latency. How many contradictory episodes or how much time elapses before a stale concept is 
contested or revised?
Lineage correctness. Do revisions, merges, and splits preserve accurate parent and evidence links?
Calibration. Does stated confidence correspond to observed concept correctness and application success? 
Brier score and expected calibration error will be reported.
Efficiency metrics
• input and output tokens per episode and per decision;
• model calls per accepted concept;
• storage growth;
• median and tail latency;
• energy or hardware-time proxy where measurable;
• task utility per 1,000 retrieved tokens.
7.6 Human evaluation
Concept quality cannot be reduced entirely to lexical matching. A stratified sample will be rated by at least 
three annotators who are blind to the system condition. The rubric covers correctness, support, scope, 
usefulness, and whether counterevidence was handled appropriately. Inter-rater agreement is reported using 
Krippendorff’s alpha. Disagreements are retained rather than resolved solely by an LLM judge.
LLM-based judges may scale evaluation, but they will be calibrated against the human sample. Prompts and 
raw judgements will be released. The same model used to generate a concept will not be the only judge of that 
concept.
7.7 Ablations
The following components are removed one at a time:
• reflection–concept separation;
• counterevidence retrieval;
• evidence diversity threshold;
• temporal validity;
• lifecycle versioning;
• application-outcome feedback;
• source-episode restoration at retrieval;
• graph associations beyond vector similarity.
Additional sweeps vary reflection frequency, promotion thresholds, retrieval budget, and confidence 
formulation.
7.8 Statistical analysis
Binary outcomes use paired tests such as McNemar’s test where appropriate. Continuous or ordinal metrics 
use paired bootstrap confidence intervals and report effect sizes. Multiple random seeds are used for synthetic 
generation and stochastic inference. The primary comparisons and practical significance thresholds are frozen 
in the experiment configuration before the sealed tests.

--- Page 16 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
16
Results are reported by task category and stream length, not only as a single average. Failure analysis separates 
write, association, reflection, consolidation, retrieval, reasoning, and application errors.
8. Open-Source Reference Implementation
8.1 Licensing
The proposed default licence split is:
• Apache License 2.0 for source code;
• CC BY 4.0 for the paper, diagrams, documentation, and synthetic benchmark content;
• third-party datasets retained under their original licences and downloaded separately.
Apache-2.0 permits commercial and research use while providing an explicit patent grant. The starter 
repository includes root licence files, a NOTICE file, and machine-readable CITATION.cff; source-file SPDX 
headers and generated dependency attribution are required before an archival release.
8.2 Repository structure
experience-learning-layer/
├── README.md
├── LICENSE
├── CITATION.cff
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── GOVERNANCE.md
├── pyproject.toml
├── paper/
│   ├── paper.md
│   ├── main.tex
│   ├── references.bib
│   ├── figures/
│   └── sections/
├── src/ell/
│   ├── models.py
│   ├── interfaces.py
│   ├── reflection/
│   ├── concepts/
│   ├── retrieval/
│   ├── evaluation/
│   ├── storage/
│   └── providers/
├── schemas/
├── benchmarks/
│   └── synthetic/
├── examples/
├── tests/
└── docs/
The starter repository included with this draft contains typed domain models, interfaces, an in-memory store, 
deterministic baseline engines, evaluation utilities, a minimal example, and tests. It is a scaffold rather than the 
completed research system.
8.3 Reproducibility requirements
Every reported experiment must include:

--- Page 17 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
17
• immutable configuration files;
• exact Git commit;
• model identifiers and hashes where available;
• prompts and structured-output schemas;
• random seeds;
• hardware and serving configuration;
• raw outputs and failure logs;
• evaluation code and judge prompts;
• token, latency, and storage accounting.
A one-command small-scale reproduction should run on consumer hardware with a compact open model. Full 
benchmark results may require larger hardware, but the same code path and data format must be used.
8.4 Contribution model
The project begins with a lightweight maintainer model and public design records. Significant architecture 
decisions use short decision documents in docs/decisions/. Contributions require tests, provenance for 
benchmark changes, and a declaration when generated data or code was produced with model assistance.
Research claims are reviewed separately from software changes. A faster implementation is not accepted as 
scientifically equivalent unless its behaviour and evaluation remain comparable.
8.5 Private data boundary
Personal ChatGPT exports can be used locally to test ingestion and qualitative usefulness, but they are not part 
of the public benchmark and must not be committed. Public experiments use synthetic or properly licensed 
data. The starter repository includes data-governance guidance; redaction hooks, local namespaces, and tested 
deletion cascades are required before any longitudinal pilot.
9. Ethics, Privacy, and Security
A memory system can improve continuity while also increasing risk. Persistent concepts may encode sensitive 
information, amplify a mistaken interpretation, or influence actions long after the originating interaction. 
Long-term memory is therefore a control channel, not merely a convenience layer. Research on trustworthy 
memory search similarly shows that semantically related memory can still be inappropriate or unsafe for the 
current task (Zhang et al. 2026).
ELL adopts the following principles.
Visibility. Users should be able to inspect active concepts, evidence, uncertainty, and change history.
Correction. A user correction is stored as high-priority evidence and can trigger immediate contestation, but it 
should not silently erase historical state when historical reasoning is required.
Deletion. Source deletion propagates to derived concepts. Derived content must not survive simply because it 
was transformed.
Least access. Retrieval enforces source-level permissions and subject namespaces before semantic relevance 
is considered.
No hidden certainty. Contested or weak concepts are labelled. Confidence and evidence counts are not 
replaced by persuasive prose.
Poisoning resistance. New memories do not automatically become trusted rules. Promotion requires 
independent evidence and validators, and sensitive actions can require human approval.

--- Page 18 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
18
Purpose limitation. Concepts formed for one domain are not automatically reused in another. Cross-domain 
transfer is an explicit, auditable operation.
The system may still infer sensitive traits that were never stated directly. The research implementation 
therefore defaults to local processing, excludes sensitive-trait inference from public examples, and treats 
inferred personal concepts as user-governed data. Future work must test whether users can understand and 
meaningfully control these abstractions.
10. Limitations and Threats to Validity
First, textual concepts favour knowledge that can be expressed as propositions or instructions. Tacit motor 
skills, perceptual expertise, and distributed representations may not fit this format. ELL may therefore 
complement rather than replace parametric or executable skill learning.
Second, provenance does not guarantee truth. Episodes can be incorrect, duplicated, biased, or malicious. A 
perfectly traceable concept may still be grounded in poor evidence. Source reliability and adversarial 
robustness require separate study.
Third, LLM-generated reflections may introduce causal stories that are plausible but unsupported. The 
validation and counterevidence stages reduce this risk but cannot eliminate it. Human evaluation remains 
necessary for high-stakes domains.
Fourth, the proposed confidence formula is heuristic. Evidence counts are not independent observations, and 
application outcomes may be delayed or confounded. Calibration must be empirical and domain-specific.
Fifth, synthetic benchmarks can overstate progress if their latent rules resemble the system’s representation. 
The controlled benchmark is useful for diagnosis but must be paired with natural conversations and agentic 
tasks.
Sixth, comparisons across memory systems are difficult because ingestion granularity, retrieval budget, model 
backbone, prompts, and judge choice can dominate results. The protocol therefore fixes budgets and reports 
complete configurations, but residual implementation differences remain.
Seventh, the architecture adds cost and operational complexity. The system is unsuccessful if the concept layer 
does not deliver enough transfer, safety, or efficiency to justify reflection, validation, storage, and governance 
overhead.
Finally, cognitive analogies are limited. Human episodic and semantic memory motivate the separation of 
roles, but ELL should not be interpreted as an account of biological memory or consciousness.
11. Expected Outcomes and Falsifiability
This work is intended to produce a testable system rather than an unfalsifiable architecture diagram. The 
primary claim would be weakened or rejected under any of the following outcomes:
• concept-level metrics improve but downstream transfer does not;
• direct insight extraction matches ELL on scope and contradiction handling at lower cost;
• concepts systematically omit exceptions that episode retrieval preserves;
• confidence remains poorly calibrated across model families;
• revision creates instability or catastrophic concept churn;
• open-weight models cannot generate sufficiently reliable structured reflections;
• privacy-preserving deletion cannot remove derived information without rebuilding the store;
• performance gains disappear under equal retrieval budgets.

--- Page 19 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
19
Negative results remain useful. They can show that explicit concept objects are unnecessary for some task 
classes, that reflection should be triggered only by failures, or that evidence-grounded retrieval is more 
valuable than consolidation. The repository and benchmark are structured so that these alternatives can be 
tested without preserving the original hypothesis.
12. Research and Implementation Roadmap
Phase 0 — Specification and scaffold
• publish the paper draft, schemas, repository structure, and governance files;
• implement typed models and in-memory stores;
• provide deterministic baseline engines and unit tests;
• open public issues for unresolved design choices.
Exit criterion: a contributor can record episodes, create a reflection, promote a concept, retrieve it with 
evidence, and run the test suite locally.
Phase 1 — Controlled benchmark
• implement the latent-pattern stream generator;
• define gold concepts, evidence, counterevidence, exceptions, and change points;
• freeze metrics and annotation rubric;
• publish baseline results for raw retrieval, rolling summary, and direct insights.
Exit criterion: a complete benchmark run produces concept and downstream metrics with fixed seeds.
Phase 2 — Reflection and Concept Engines
• add structured model adapters for local open-weight inference;
• implement validation, promotion, merge, split, and revision;
• add the evidence ledger and lifecycle UI or report;
• run component ablations.
Exit criterion: ELL can be compared with baselines on the sealed synthetic test set.
Phase 3 — External benchmarks
• integrate LongMemEval and LoCoMo;
• integrate MemBench and MemoryArena where licences and compute permit;
• reproduce selected open memory baselines under equal budgets;
• complete human evaluation and calibration.
Exit criterion: results can support or reject H1–H4 across at least one conversational and one action 
benchmark.
Phase 4 — Paper completion
• replace this preregistration status with methods and results generated from tagged releases;
• add statistical analysis, failure cases, and limitations discovered in practice;
• release raw experiment artefacts and a reproducibility package;
• submit to an appropriate agent, NLP, HCI, or continual-learning venue.

13. Product Architecture Expansion

The research architecture above asks whether evidence-grounded concepts improve transfer and future behaviour. The product architecture developed after the v0.1 preregistration generalises that research scaffold into L: an open, local-first experience-learning layer usable by people, applications, and AI agents. This expansion does not replace the original empirical question. It makes the operational boundaries needed to test and eventually deploy it explicit.

L is not primarily a chatbot, note-taking application, vector database, or graph visualisation. Its product loop is to capture an experience, preserve its source, extract typed candidates, decide under deterministic policy what may become durable, consolidate related memories without losing contradictions, retrieve the smallest useful context, observe outcomes, and revise future behaviour. Models interpret meaning and propose. Deterministic services validate, authorize, version, and commit.

13.1 Plural memory semantics

The v0.1 paper distinguishes episodes, reflections, concepts, applications, and outcomes. The broader product architecture retains these objects while distinguishing additional memory semantics that have different authority, lifetime, and retrieval rules:

• source memory preserves immutable artifacts and exact addressable spans;
• working memory holds expiring state for the current task or conversation;
• episodic memory represents bounded experiences, decisions, actions, and outcomes;
• semantic memory represents temporal assertions rather than timeless key-value pairs;
• preference memory represents scoped choices, exceptions, strength, and explicitness;
• procedural memory represents versioned workflows, preconditions, approvals, evidence, and rollback;
• prospective memory represents commitments, reminders, deadlines, and unresolved threads;
• relational memory represents evidence-backed temporal edges;
• reflective memory records uncertainty, freshness, usefulness, contradictions, and knowledge gaps;
• policy memory defines retention, consent, provider, sharing, and deletion boundaries and is never ordinary model context.

These forms may share infrastructure, but they must not be flattened into one untyped table with identical lifecycle semantics. The useful product is the explainable connection layer, not a decorative node cloud.

13.2 Source, event, and episode boundary

All provider connectors terminate at a common normalization boundary. An immutable SourceArtifact preserves source identity, checksums, timestamps, sensitivity, consent, and stable spans. Normalized ExperienceEvents represent user messages, assistant messages, tool calls and results, file changes, decisions, feedback, and external events. One or more events form a bounded Episode containing inputs, responses, actions, observations, and outcomes.

Stable deterministic identifiers make ingestion rerunnable. The same connector, external reference, source version, and source event produce the same domain IDs. A ChatGPT export, Codex App Server stream, calendar connector, or future provider can therefore be replaced without placing its schema inside reflection, consolidation, policy, or retrieval services.

Historical consumer ChatGPT history is acquired through documented exports rather than undocumented APIs. A future live Codex source may map thread, turn, item, tool, and result events into the same boundary. ChatGPT account access through a Codex runtime is not treated as arbitrary access to consumer ChatGPT history.

13.3 Governed candidate and commit path

A model response is untrusted structured input. It enters a CandidateMemory quarantine and cannot participate in normal retrieval. Deterministic validation checks the schema, cited source and span existence, workspace access, sensitivity inheritance, temporal fields, allowed predicates, and referenced memories. Policy then selects one of three initial outcomes:

• explicit user statements, corrections, and user-confirmed candidates may commit after validation;
• supported ordinary inferences and inferred procedures wait for review;
• unsupported non-explicit claims and sensitive model inferences are rejected.

The commit service is the sole canonical writer. It uses idempotency keys and optimistic concurrency, writes an immutable revision, appends a content-minimized audit event, and schedules disposable projections. A correction creates a new memory and closes the validity of the superseded revision. It never rewrites history. A lower-authority inference cannot supersede explicit user evidence.

13.4 Policy-bound evidence retrieval

Retrieval is a typed service rather than direct database or vector-index access. A request includes actor, purpose, workspace, scope, allowed memory types, maximum sensitivity, evidence preference, and a fixed context budget. Authorization and lifecycle filtering happen before relevance ranking. Superseded, forgotten, expired, cross-workspace, and sensitivity-incompatible records do not enter ordinary results.

Candidate generation may combine lexical search, vectors, relation neighbourhoods, time, pinning, procedures, and later learned rerankers. Exact-vector, HNSW, and TurboVec indexes remain replaceable projections to benchmark; no index is canonical memory. The response is an EvidencePacket containing selected current claims, scoped preferences, episodes, procedures, commitments, citations, selection explanations, uncertainty, and known material contradictions. A compact concept never becomes a naked instruction detached from its source.

13.5 Local-first and provider-neutral topology

A complete usable state can live on one device. Network absence must not prevent capture, browsing, correction, or lexical retrieval. Remote processing visibly degrades to local processors or queued work. A practical reference adapter may use SQLite, content-addressed encrypted files, FTS5, and a replaceable vector index, but these technologies do not define the domain.

Four authentication concerns remain separate: L user identity, workspace authorization, model-provider credentials, and connector grants. OpenAI and Codex integration likewise has distinct directions: L may call a model API; ChatGPT, Codex, or another client may call L through MCP; L may optionally supervise a documented local Codex runtime; or L may export a scoped context bundle. An API key is not an L login, and a consumer ChatGPT subscription is not assumed to create a third-party application credential.

Forgetting immediately excludes a record, writes a tombstone, removes projections, and triggers evidence-aware invalidation. Sync must not resurrect tombstoned content. Sensitive trait inference is disabled for automatic durable learning. Imported documents are untrusted content, never system instructions. Secrets do not enter prompts, canonical memory, exports, analytics, or logs.

14. Reference Implementation Status

The repository now contains an executable Phase 0 proof aligned with the expanded architecture. This is implementation evidence, not an empirical result for H1-H4.

14.1 Versioned contracts and deterministic identity

Immutable Pydantic boundary models define SourceArtifact, SourceSpan, ExperienceEvent, Episode, CandidateMemory, MemoryRecord, AuditEvent, RetrievalRequest, and EvidencePacket. A registry exposes draft 2020-12 JSON Schemas with stable v1 identifiers and rejects unknown schema versions. Deterministic UUID derivation covers sources, events, and episodes so normalization can be rerun without changing identity.

14.2 Pure governed kernel

The LearningKernel runs without a database, network, or model. In-memory reference adapters implement artifact storage, candidate quarantine, immutable memory revisions, optimistic concurrency, idempotent mutation results, and append-only audit events. The deterministic policy and commit path enforce evidence, workspace, sensitivity, authority, correction, contradiction, forgetting, and retrieval lifecycle rules.

A fixture-backed DeterministicMockProvider advertises provider-neutral capabilities and validates every configured response against the requested Pydantic model. Missing or malformed fixtures fail loudly. It performs no network I/O and cannot invent a fallback response.

14.3 Golden evaluation corpus

The versioned synthetic corpus covers explicit scoped preferences, single-event inference, unsupported claims, sensitive inference, explicit correction, material contradiction, temporal change, Dutch evidence, and prompt injection embedded in imported content. Each JSONL case has a stable ID, exact evidence excerpt, typed candidate description, and expected policy or lifecycle outcome. Corpus validation rejects malformed or duplicate cases.

At this revision, the paper-first repository contains 31 passing Python tests and 3 passing Swift tests. Strict static type checking passes for 14 Python source files, repository-wide Ruff lint passes, and the macOS client passes Swift formatting checks. The disconnected web, database, provider, and TencentDB scaffolding from the initial repository remains outside the canonical kernel; the new client is a narrow Phase 1 adapter over the existing source, event, and episode contracts.

14.4 Remaining gates

The in-memory proof does not yet demonstrate persistent SQLite rebuilds, deletion propagation through projections, encrypted sync, extension capability isolation, provider egress enforcement, job checkpoint recovery, or live cross-client operation. Those invariants are explicit deferred release gates for the phases that introduce the relevant adapters. The first Phase 1 preview adds a macOS chat connector, append-only local source/event/episode JSONL, deterministic completed-turn boundaries, a fixture provider, and an OpenAI-ready provider seam. This is input-pipeline evidence rather than a result for H1-H4. Incremental ChatGPT export import, SQLite, association indexes, and comparative TencentDB or hosted-memory evaluation remain subsequent Phase 1 work behind stable ports.

15. Conclusion
The Experience Learning Layer begins from a simple distinction: access to old experience is not the same as 
learning from it. Current research already demonstrates reflection, dynamic memory organisation, schema 
induction, concept graphs, and semantic or procedural abstraction. The next useful contribution is therefore a 
stricter account of how an abstraction earns trust, remains connected to evidence, changes when challenged, 
and improves future behaviour.
ELL proposes an explicit path from episodes to provisional reflections, from reflections to versioned concepts, 
and from concepts to measured applications and outcomes. The architecture preserves both support and 
counterevidence, treats scope and temporal validity as first-class fields, and makes revision reversible and 
auditable. Its value will be determined empirically, not by the plausibility of the design.
The project is open by default. The paper, schemas, benchmark generator, implementation, prompts, and 
evaluation harness are intended to make the research easy to inspect, reproduce, criticise, and extend. The 
immediate next step is not to claim a finished learning system, but to build the controlled benchmark and 
reference implementation needed to test whether the proposed lifecycle actually works.
Acknowledgements
This working draft was developed as part of the open Experience Learning Layer project. Future versions will 
list contributors according to documented authorship and contribution criteria.

--- Page 21 ---
EXPERIENCE LEARNING LAYER  ·  WORKING DRAFT v0.1
21
References
Bartlett, Frederic C. 1932. Remembering: A Study in Experimental and Social Psychology. Cambridge University Press.
Fei, Tianxiang, Mingyang Song, Mao Zheng, and Xiang Yu. 2026. ‘Memory Beyond Recall: A Dual-Process Cognitive Memory System 
for Self-Evolving LLM Agents’. https://arxiv.org/abs/2606.09483.
He, Zexue, Yu Wang, Churan Zhi, Yuanzhe Hu, Tzu-Ping Chen, Lang Yin, Ze Chen, et al. 2026. ‘MemoryArena: Benchmarking Agent 
Memory in Interdependent Multi-Session Agentic Tasks’. https://arxiv.org/abs/2602.16313.
Kumaran, Dharshan, Demis Hassabis, and James L. McClelland. 2016. ‘What Learning Systems Do Intelligent Agents Need? 
Complementary Learning Systems Theory Updated’. Trends in Cognitive Sciences 20 (7): 512–34. 
https://doi.org/10.1016/j.tics.2016.05.004.
Maharana, Adyasha, Dong-Ho Lee, Sergey Tulyakov, Mohit Bansal, Francesco Barbieri, and Yuwei Fang. 2024. ‘Evaluating Very 
Long-Term Conversational Memory of LLM Agents’. In Proceedings of the 62nd Annual Meeting of the Association for 
Computational Linguistics, 13851–70. https://doi.org/10.18653/v1/2024.acl-long.747.
McClelland, James L., Bruce L. McNaughton, and Randall C. O’Reilly. 1995. ‘Why There Are Complementary Learning Systems in the 
Hippocampus and Neocortex: Insights from the Successes and Failures of Connectionist Models of Learning and Memory’. 
Psychological Review 102 (3): 419–57. https://doi.org/10.1037/0033-295X.102.3.419.
Packer, Charles, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Ion Stoica, and Joseph E. Gonzalez. 2023. ‘MemGPT: 
Towards LLMs as Operating Systems’. https://arxiv.org/abs/2310.08560.
Park, Joon Sung, Joseph C. O’Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, and Michael S. Bernstein. 2023. ‘Generative 
Agents: Interactive Simulacra of Human Behavior’. In Proceedings of the 36th Annual ACM Symposium on User Interface 
Software and Technology, 1–22. https://doi.org/10.1145/3586183.3606763.
Paul, Swarna Kamal, Shubhendu Sharma, and Nitin Sareen. 2026. ‘GAAMA: Graph Augmented Associative Memory for Agents’. 
https://arxiv.org/abs/2603.27910.
Rasmussen, Preston, Pavlo Paliychuk, Travis Beauvais, Jack Ryan, and Daniel Chalef. 2025. ‘Zep: A Temporal Knowledge Graph 
Architecture for Agent Memory’. https://arxiv.org/abs/2501.13956.
Shinn, Noah, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. 2023. ‘Reflexion: Language 
Agents with Verbal Reinforcement Learning’. In Advances in Neural Information Processing Systems. Vol. 36. 
https://arxiv.org/abs/2303.11366.
Su, Miao, Yucan Guo, Zhongni Hou, Long Bai, Zixuan Li, Yufei Zhang, Guojun Yin, et al. 2026. ‘Beyond Dialogue Time: Temporal 
Semantic Memory for Personalized LLM Agents’. https://arxiv.org/abs/2601.07468.
Sumers, Theodore R., Shunyu Yao, Karthik Narasimhan, and Thomas L. Griffiths. 2024. ‘Cognitive Architectures for Language Agents’. 
Transactions on Machine Learning Research. https://arxiv.org/abs/2309.02427.
Tan, Haoran, Zeyu Zhang, Chen Ma, Xu Chen, Quanyu Dai, and Zhenhua Dong. 2025. ‘MemBench: Towards More Comprehensive 
Evaluation on the Memory of LLM-Based Agents’. In Findings of the Association for Computational Linguistics: ACL 2025. 
https://arxiv.org/abs/2506.21605.
Tan, Zhen, Jun Yan, I-Hung Hsu, Rujun Han, Zifeng Wang, Long T. Le, Yiwen Song, et al. 2025. ‘In Prospect and Retrospect: 
Reflective Memory Management for Long-Term Personalized Dialogue Agents’. In Proceedings of the 63rd Annual Meeting of the 
Association for Computational Linguistics, 8416–39. https://doi.org/10.18653/v1/2025.acl-long.413.
Tulving, Endel. 1972. ‘Episodic and Semantic Memory’. In Organization of Memory, edited by Endel Tulving and Wayne Donaldson, 
381–403. Academic Press.
Wang, Guanzhi, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke Zhu, Linxi Fan, and Anima Anandkumar. 2023. 
‘Voyager: An Open-Ended Embodied Agent with Large Language Models’. In Transactions on Machine Learning Research. 
https://arxiv.org/abs/2305.16291.
Wang, Zora Zhiruo, Jiayuan Mao, Daniel Fried, and Graham Neubig. 2025. ‘Agent Workflow Memory’. In Proceedings of the 42nd 
International Conference on Machine Learning, 267:63897–911. Proceedings of Machine Learning Research.
Wu, Di, Hongwei Wang, Wenhao Yu, Yuwei Zhang, Kai-Wei Chang, and Dong Yu. 2025. ‘LongMemEval: Benchmarking Chat 
Assistants on Long-Term Interactive Memory’. In International Conference on Learning Representations. 
https://arxiv.org/abs/2410.10813.
Xu, Wujiang, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, and Yongfeng Zhang. 2025. ‘A-MEM: Agentic Memory for LLM Agents’. 
In Advances in Neural Information Processing Systems. https://arxiv.org/abs/2502.12110.
Yang, Ke, Zixi Chen, Xuan He, Jize Jiang, Michel Galley, Chenglong Wang, Jianfeng Gao, Jiawei Han, and ChengXiang Zhai. 2026. 
‘PlugMem: A Task-Agnostic Plugin Memory Module for LLM Agents’. https://arxiv.org/abs/2603.03296.
Zhang, Jiawen, Kejia Chen, Jiachen Ma, Yangfan Hu, Lipeng He, Yechao Zhang, Jian Liu, Xiaohu Yang, Tianwei Zhang, and Ruoxi Jia. 
2026. ‘Beyond Similarity: Trustworthy Memory Search for Personal AI Agents’. https://arxiv.org/abs/2606.06054.
Zhao, Andrew, Daniel Huang, Quentin Xu, Matthieu Lin, Yong-Jin Liu, and Gao Huang. 2024. ‘ExpeL: LLM Agents Are Experiential 
Learners’. In Proceedings of the AAAI Conference on Artificial Intelligence, 38:19632–42. 17. 
https://doi.org/10.1609/aaai.v38i17.29936.
Zhong, Wanjun, Lianghong Guo, Qiqi Gao, He Ye, and Yanlin Wang. 2024. ‘MemoryBank: Enhancing Large Language Models with 
Long-Term Memory’. In Proceedings of the AAAI Conference on Artificial Intelligence, 38:19724–31. 17. 
https://doi.org/10.1609/aaai.v38i17.29946.
