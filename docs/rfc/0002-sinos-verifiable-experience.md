---
title: "RFC 0002 — Sinos as a Verifiable Problem-Solving Framework for Raw Experiences"
status: proposed
created: 2026-09-02
---

# RFC 0002 — Sinos as a Verifiable Problem-Solving Framework for Raw Experiences

## Summary

This RFC proposes a deeper integration between WikiSkill and Sinos (`franklinbaldo/sinustdd`).

Sinos should evolve from a framework specialized in proving causal TDD order into an optional framework for **verifiable problem-solving trajectories**. A problem is represented as an initial state that is demonstrably RED with respect to a success condition, plus invariants, admissible transformations, and evidence requirements. An agent acts on that problem until it either reaches a demonstrably GREEN state or terminates with an explicitly unresolved obligation.

The important WikiSkill output is not Sinos' internal ledger. It is a standardized **Experience report authored by the agent**, persisted in WikiSkill's raw-experience layer and constrained by evidence collected during the trajectory.

The intended pipeline is:

```text
Sinos
state + obligation + trajectory + witnesses + evidence
        ↓
WikiSkill raw Experience
agent-authored report of what happened
        ↓
WikiSkill wiki
knowledge consolidated across experiences
        ↓
WikiSkill skills
reusable procedures evolved from persistent knowledge
```

TDD remains a first-class specialization of the model, but is no longer its conceptual limit.

Lean may be used as an optional high-assurance verification layer for problems that benefit from explicit state, invariants, predicates, and proofs. It is not required for every problem and does not turn WikiSkill into a theorem-proving system.

Tracking issue: #24.

## Relationship to the WikiSkill paper

The primary theoretical reference remains:

**Liyan Tang, Cyrus Rashtchian, Chun-Sung Ferng, Andrew Tomkins, Da-Cheng Juan, Tu Vu. _WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution_. 2026.**

Canonical preprint:

<https://arxiv.org/abs/2608.27454>

The paper supplies the core separation between:

1. raw agent execution experience;
2. accumulated persistent wiki knowledge;
3. executable skills.

This RFC does **not** claim that the paper defines Sinos, RED/GREEN obligations, Lean formalization, proof-carrying trajectories, Git/GitHub witnesses, or the report schema proposed here. Those are engineering extensions of this project.

A particularly important interpretation is:

> In WikiSkill, `raw` means **experience that has not yet been consolidated into persistent wiki knowledge**. It does not mean uninterpreted machine telemetry.

A raw Experience is therefore allowed to be an agent report containing decisions, explanations, uncertainty, and learning. Machine-generated evidence may support the report, but machine output is not itself the semantic definition of an Experience.

## Problem

WikiSkill depends on the quality of the Experiences from which it learns.

An unconstrained post-hoc report has several failure modes:

- the agent may omit important intermediate states;
- intent may be confused with outcome;
- causal order may be reconstructed incorrectly;
- a verification may be described as having happened when it did not;
- failed attempts may disappear from the narrative;
- uncertainty may be rewritten as fact;
- two semantically similar executions may be recorded in incompatible shapes;
- later consolidation may treat a confident narrative as stronger evidence than it deserves.

Sinos already addresses one instance of this problem for TDD: it distinguishes a real RED-before-GREEN causal trajectory from a narrative written after the implementation already exists.

This RFC generalizes that idea.

Many agent tasks outside traditional software testing still have:

- an observable initial state;
- a desired state;
- properties that can be checked;
- invariants that should survive the work;
- actions that transform the state;
- evidence that can support or reject claims about those transformations.

Examples include:

- repairing a pull request until it is merge-eligible;
- producing a news article until provenance gates are satisfied;
- reconciling a dataset until coverage and consistency invariants hold;
- preparing a legal or operational document until required conditions are present;
- migrating a repository while preserving declared invariants;
- resolving an implementation task until a test suite is green.

The opportunity is to make these trajectories produce **comparable, evidence-constrained raw Experiences** for WikiSkill.

## Product thesis

WikiSkill learns from experience.

Sinos should make problem-solving experience easier to:

- structure;
- verify;
- compare;
- audit;
- persist honestly;
- consolidate later.

The core relationship is:

```text
Sinos = execution protocol + state transitions + witnesses
WikiSkill Experience = agent report constrained by that protocol
WikiSkill wiki = cross-experience consolidation
WikiSkill skill = reusable behavior derived from accumulated knowledge
```

Sinos does not replace WikiSkill's Experience concept.

Sinos helps the agent generate a better Experience.

## Terminology

### Experience

A primary report of one concrete agent execution.

It answers questions such as:

- what was the objective?
- what state did the agent encounter?
- what did the agent believe was blocking success?
- what actions did it take?
- what happened after each important action?
- what was actually verified?
- what remained uncertain?
- what did the agent learn?

An Experience is raw with respect to **consolidation**, not with respect to interpretation.

### Obligation

A verifiable unit of problem-solving work.

Conceptually:

```text
Obligation
  ├── objective
  ├── initial_state
  ├── green_condition
  ├── invariants
  ├── admissible_actions / transformations
  ├── evidence_requirements
  └── verification_level
```

Not every field must always be formal or exhaustive. The model should degrade gracefully when only part of the problem is machine-verifiable.

### RED

An initial or intermediate state that is demonstrably not GREEN with respect to the declared obligation.

Crucially:

> Failure to prove GREEN is not proof of RED.

Where possible, RED should be supported by:

- a decidable predicate evaluating to false;
- an explicit counterexample;
- a deterministic failed check;
- or a formal proof of `¬ Green(state)`.

### GREEN

A state that satisfies the declared success condition under the declared verification mechanism.

GREEN is always relative to the obligation. It does not mean that the world is globally correct or that no unmodeled defect remains.

### Invariant

A property that must remain true while moving from RED toward GREEN.

Examples:

- existing tests must remain unchanged after RED is frozen;
- a data migration must preserve all unrelated rows;
- a pull-request repair must preserve intended behavior;
- a news article must not introduce unsupported factual claims;
- a legal document must retain mandatory content while another defect is repaired.

### Witness

Evidence supporting a claim about a state or transition.

Examples include:

- command exit status;
- test results;
- Git object identity;
- API state;
- schema-validation result;
- source-document citation;
- Lean proof term;
- deterministic predicate evaluation.

### Trajectory

The sequence of relevant observations, decisions, actions, resulting states, and witnesses between the beginning and end of an obligation.

## General execution model

The generalized Sinos loop is:

```text
OBSERVE
   ↓
MODEL / FORMALIZE
   ↓
ESTABLISH RED
   ↓
CHOOSE NEXT TRANSFORMATION
   ↓
VERIFY THAT IT IS ADMISSIBLE
   ↓
ACT
   ↓
OBSERVE AGAIN
   ↓
VERIFY TRANSITION / INVARIANTS
   ↓
... repeat ...
   ↓
ESTABLISH GREEN
   ↓
GENERATE EXPERIENCE REPORT
```

This should not require every implementation to expose every box as a separate command. The semantic requirement is that the resulting Experience can distinguish:

- what was observed;
- what was modeled;
- what was inferred;
- what was attempted;
- what changed;
- what was verified;
- what remains uncertain.

## TDD as one specialization

Traditional Sinos behavior becomes one profile of the general model:

```text
State
  = checkout + implementation + verification files

Green
  = verification suite passes

RED witness
  = newly introduced verification fails before production implementation

Invariant
  = frozen RED contract is not weakened during GREEN

Action
  = production change

Green witness
  = same frozen obligation now passes
```

This specialization should remain ergonomic and opinionated. Generalization must not weaken the existing causal TDD guarantees.

## Non-code example: pull-request repair

A pull request may be represented as:

```text
Initial state
- merge conflict exists
- one required check is failing
- no blocking review exists

Green
- mergeable
- all required checks green
- no blocking reviews

Invariants
- intended feature behavior remains
- unrelated changes are not introduced

Possible trajectory
1. observe conflict
2. inspect semantic difference against current main
3. resolve conflict
4. verify intended diff remains
5. observe required check failure
6. repair cause
7. re-run verification
8. observe remote PR state
9. establish GREEN
```

The Experience should report both the agent's reasoning and the concrete evidence that supports strong claims such as “all required checks were green”.

## Non-code example: verifiable journalism

An editorial obligation may be:

```text
Initial state
- draft contains a factual claim without admissible provenance

Green
- all material factual claims have acceptable provenance
- required editorial gates pass

Invariants
- source text is not misrepresented
- uncertainty is not silently converted into fact

Possible trajectory
1. identify unsupported claim
2. locate candidate source
3. inspect source
4. compare source to wording
5. narrow or correct claim
6. attach provenance
7. rerun editorial gates
8. establish GREEN or record unresolved uncertainty
```

Nothing about this problem is “mathematical” in ordinary language, but parts of it are still verifiable.

## Verification levels

Not every obligation deserves the same machinery.

The framework should support at least three levels.

### `simple`

A deterministic mechanism directly checks the condition.

Examples:

- command exit code;
- schema validation;
- file presence;
- API status;
- CI check state.

### `predicate`

The problem is represented by structured state and a composed success predicate.

Example:

```text
mergeable(pr)
AND required_checks_green(pr)
AND blocking_reviews(pr) = 0
```

The implementation may use ordinary code rather than a proof assistant, as long as the evaluator and inputs are explicit enough to audit.

### `formal`

State, invariants, success predicates, and/or allowed transitions are represented in a formal system such as Lean.

This level is appropriate when:

- many variables interact;
- preserving invariants is difficult;
- the search space is large;
- a proof object is materially more useful than an ordinary boolean check;
- a generated executable test would otherwise only approximate the intended property.

Lean is an optional verification engine, not a universal requirement.

## Natural language to formal obligation

For suitable problems, Sinos may assist the agent in translating natural-language intent into a formal model.

Conceptually:

```text
natural-language problem
        ↓
state model
        ↓
green predicate
        ↓
invariants
        ↓
examples / counterexamples
        ↓
formal elaboration
        ↓
RED witness
```

A Lean representation may resemble:

```lean
structure State where
  -- relevant variables

def Green (s : State) : Prop :=
  -- success condition

inductive Action
  | ...

def Step (before : State) (action : Action) (after : State) : Prop :=
  -- admissible transition relation
```

The agent's task can then be understood as constructing a trajectory from an initial `s₀` with a real RED witness to some reachable `sₙ` satisfying `Green sₙ`, while preserving declared invariants.

## The semantic-gap rule

Formal correctness does not prove that the model faithfully represents the user's real-world intent.

A theorem prover can prove the wrong proposition perfectly.

Therefore, formalization must preserve the semantic bridge back to the original problem.

When `verification_level: formal` is used, the report should retain, when applicable:

- original natural-language objective;
- formal state definition;
- GREEN predicate;
- invariants;
- assumptions;
- positive examples;
- counterexamples;
- unresolved ambiguities;
- provenance of externally observed facts.

The system should not silently replace a natural-language requirement with a stronger, weaker, or merely different formal statement.

## World-to-model boundary

Lean or any other verifier operates over a model. External facts still need trustworthy acquisition.

The boundary should be explicit:

```text
WORLD
  ↓ observation
TOOL / SENSOR / SOURCE
  ↓ evidence or certificate
STRUCTURED OR FORMAL STATE
  ↓ reasoning / verification
ACTION
  ↓
WORLD
  ↓ new observation
```

For example, Lean may reason from `requiredChecksGreen = true`, but it does not independently know the live state of GitHub. The observation supplying that value needs provenance.

This distinction should survive into the Experience.

## Provenance classes inside an Experience

Claims in a generated Experience should be distinguishable as at least:

- `observed` — directly obtained from a tool, command, source, or external system;
- `verified` — checked by a deterministic or formal mechanism;
- `inferred` — concluded by the agent from available evidence;
- `reported` — supplied by an external actor/source but not independently verified;
- `uncertain` — still ambiguous, hypothetical, or unresolved.

This classification may be represented structurally rather than repeated as literal labels in every paragraph. The important property is that later consolidation can avoid treating every sentence as equally authoritative.

## What Sinos should generate

Sinos should not merely dump machine telemetry into WikiSkill.

At the end of an obligation, Sinos should provide enough structured context for the **agent to author a standardized Experience report**.

A minimum report shape is:

```text
# Objective
What the agent was trying to achieve.

# Initial state
What the agent encountered before acting.

# Green condition
How success was defined and checked.

# Invariants
What was required to remain true.

# Red witness
Why the initial state was demonstrably not GREEN.

# Trajectory
For each meaningful step:
- observation
- decision
- action
- justification
- result
- witness, when applicable

# Proof obligations
Formal or otherwise verifiable sub-obligations discovered during work.

# Evidence
Evidence supporting important factual or causal claims.

# Final state
The last observed state.

# Green witness
Why the final state satisfies GREEN, if it does.

# Learnings
What this execution taught the agent.

# Residual uncertainty
What remains unverified, ambiguous, or outside the model.
```

The exact prose remains authored by the agent. Sinos supplies structure and evidence constraints.

## Failed and incomplete trajectories are valid Experiences

WikiSkill should learn from failures, not only successes.

An obligation may terminate without GREEN because:

- a required external dependency is unavailable;
- the modeled approach is wrong;
- a formal obligation cannot be discharged;
- a tool cannot obtain required evidence;
- a proposed transformation violates an invariant;
- the task is discovered to be underspecified;
- execution is intentionally abandoned.

The resulting Experience should still preserve:

- confirmed RED state;
- actions attempted;
- intermediate observations;
- failed proof obligations;
- latest known state;
- reason for termination;
- residual uncertainty;
- useful learning.

The report must not manufacture GREEN merely to make the trajectory look complete.

## Anti-post-hoc guarantees

The Experience may be written at the end of a session, but strong causal claims should be backed by witnesses captured while the trajectory was occurring.

Claims that should not rely on narrative alone include, for example:

- “the test failed before production code changed”;
- “the formal contract was unchanged between RED and GREEN”;
- “all required PR checks were green”;
- “the source supported this claim at publication time”;
- “this transformation preserved the declared invariant”.

When Sinos cannot verify such a statement, the Experience should record it as inferred, reported, or uncertain rather than verified.

## Freezing the obligation

Once RED is established, semantically important parts of the obligation should not be silently weakened to manufacture GREEN.

Depending on the verification mode, Sinos may freeze digests of:

- natural-language objective;
- formal contract;
- GREEN predicate;
- invariants;
- generated verification tests;
- relevant initial state;
- verification mechanism.

Clarifying or legitimately changing the objective is allowed, but it should create a new revision of the obligation or otherwise make the change explicit in the trajectory.

This is the generalized analogue of preventing an agent from changing a RED test to make an implementation pass.

## Internal Sinos evidence versus WikiSkill Experience

Sinos may maintain internal evidence artifacts required for causal verification, such as:

- hashes;
- Git ancestry information;
- execution results;
- diffs;
- test identities;
- proof objects;
- state snapshots;
- transition certificates.

These artifacts are not automatically WikiSkill Experiences.

The relationship is:

```text
Sinos evidence
   ↓ supports / constrains
agent-authored Experience
```

The durable semantic memory for WikiSkill remains its Experience layer.

The architecture should avoid creating a second human-semantic history that competes with WikiSkill `raw`.

## Physical layout

This RFC intentionally does not require a final directory topology.

Conceptually the output belongs to WikiSkill's raw Experience layer, for example:

```text
raw/
  <experience-id>.md
```

or:

```text
raw/
  <run-id>/
    experience.md
```

The current project may continue using another physical location while the schema and runtime stabilize. Semantic identity matters more than prematurely fixing directory names.

Likewise, Sinos internal evidence may remain in its own operational namespace when needed.

## Contract between Sinos and WikiSkill

The integration contract should remain narrow.

Sinos should be able to expose a structured obligation report containing, where available:

```text
obligation_id
objective
initial_state
green_condition
invariants
red_witness
trajectory[]
proof_obligations[]
evidence[]
final_state
green_witness
learnings
residual_uncertainty
verification_level
```

WikiSkill should be able to transform or persist that report as a valid Experience under its own schema.

WikiSkill should **not** require importing the Sinos runtime merely to read old Experiences.

Acceptable integration surfaces include:

- CLI;
- MCP;
- an OKF document;
- a stable library API;
- another explicit interchange format if justified.

The persisted Experience must remain understandable without reconstructing the entire live Sinos runtime.

## Relationship to `record_experience`

The current WikiSkill Experience-recording work remains useful.

This RFC extends the intended producer side:

```text
agent works under Sinos protocol
        ↓
Sinos accumulates obligation + witnesses + trajectory
        ↓
agent produces Experience report
        ↓
WikiSkill record_experience persists and validates it
```

`record_experience` should remain usable for Experiences that did not originate from Sinos.

Sinos is an optional high-quality producer of Experiences, not a mandatory dependency for all WikiSkill operation.

## Consolidation consequences

Standardized trajectories should improve WikiSkill's ability to discover recurring structures across superficially unrelated tasks.

For example, all of these may instantiate the same abstract pattern:

```text
required evidence missing
→ locate candidate evidence
→ validate evidence
→ update state
→ re-evaluate obligation
→ GREEN
```

The concrete domains might be:

- a failing CI check;
- a missing legal document;
- an unsupported journalistic claim;
- an incomplete dataset;
- a missing provenance edge.

WikiSkill can consolidate such recurrence into wiki knowledge and only later decide whether it deserves promotion into an executable skill.

Standardization must not erase domain details. It supplies a common backbone, not a lossy compression format.

## Implementation phases

### Phase 1 — obligation model and report generation

Extend Sinos with a generic internal `Obligation` model while preserving the existing TDD profile.

Deliver:

- objective;
- initial state;
- GREEN condition;
- invariants;
- trajectory events;
- witnesses;
- final state;
- residual uncertainty;
- generated Experience report input.

Dogfood this first on ordinary TDD work.

### Phase 2 — generic deterministic verifiers

Support non-TDD obligations using ordinary deterministic verification.

Candidate mechanisms:

- commands;
- schemas;
- repository state;
- APIs;
- composed predicates.

Demonstrate at least one real non-code obligation.

### Phase 3 — optional Lean formalization

Add a `formal` verification mode that can represent:

- state;
- GREEN predicate;
- invariants;
- allowed transitions;
- proof obligations.

Preserve the natural-language requirement and semantic examples alongside the formalization.

The goal is not “prove everything”. The goal is to support high-assurance trajectories where formal constraints materially help.

### Phase 4 — WikiSkill consolidation experiment

Generate multiple real Experiences through Sinos and test whether their standardized structure improves:

- retrieval;
- comparison;
- consolidation;
- provenance tracking;
- skill evolution.

The integration is successful only if the resulting Experiences are more useful to later agents, not merely more elaborate.

## Demonstration criteria

The RFC should be considered empirically demonstrated when the system can run at least three real obligations from materially different domains:

1. a software TDD task;
2. a repository/GitHub task;
3. a non-code task with verifiable requirements.

For each obligation the system should:

- establish RED without confusing missing proof with falsity;
- record a structured trajectory;
- preserve declared invariants or explicitly report violations;
- establish GREEN or honestly terminate incomplete;
- generate a valid WikiSkill Experience;
- distinguish observed, verified, inferred, reported, and uncertain claims;
- allow later WikiSkill tooling to compare the Experiences without losing domain-specific detail.

At least one additional experiment should use `verification_level: formal` with Lean on a problem involving multiple interacting variables and nontrivial invariants.

## Non-goals

This RFC does not propose:

- making Lean mandatory for WikiSkill;
- making every problem mathematically formal in advance;
- replacing real-world observation with theorem proving;
- treating machine logs as the semantic definition of `raw`;
- replacing agent-authored Experience reports with telemetry dumps;
- making Sinos a hard runtime dependency of WikiSkill;
- creating a second persistent semantic memory beside WikiSkill raw/wiki/skills;
- treating absence of a proof as proof of RED;
- claiming a formal model automatically captures human intent;
- promoting every Experience directly into a skill.

## Open questions

1. Should the interchange object itself be an `Experience`, an `ObligationReport`, or an `ObligationReport` that WikiSkill compiles into `Experience`?
2. Which parts of Sinos internal evidence should be referenced by digest versus embedded into the Experience?
3. Should obligation revisions form an explicit lineage when the natural-language objective is clarified?
4. Which GREEN predicates must be decidable, and which may remain externally witnessed?
5. How should WikiSkill score or represent confidence when an Experience mixes verified and inferred claims?
6. What is the smallest useful Lean contract for a real multi-variable problem without over-formalizing the domain?
7. Should a trajectory event be a first-class OKF concept or remain nested inside an Experience?
8. How much report structure should be mandatory before standardization begins to reduce rather than improve agent expression?
9. How should Sinos issue #24's “single durable causal history” direction interact with this RFC's distinction between internal evidence and WikiSkill semantic memory?

## Proposed decision

Adopt Sinos as an **optional verifiable problem-solving and Experience-generation framework** for WikiSkill.

Generalize the conceptual RED → GREEN model from test-driven development to domain-general obligations that have observable state and some verifiable success criterion.

Keep the WikiSkill boundary explicit:

- Sinos structures the trajectory and supplies witnesses;
- the agent authors the raw Experience report;
- WikiSkill persists and validates the Experience;
- WikiSkill consolidates many Experiences into wiki knowledge;
- skills evolve only from accumulated knowledge plus evaluation.

Use Lean as an optional high-assurance verification level for problems with many interacting variables, invariants, or transformations where formalization provides real value.

The central design principle is:

> **Sinos should make agent experience more verifiable without making the agent report cease to be an Experience.**
