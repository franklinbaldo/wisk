---
type: ConceptSpecification
concept_type: RuntimeRFC
description: "Canonical learning cycle across Experience, Wiki, and Skill sessions."
---

# RFC 0004 — Canonical Experience → Wiki → Skill cycle

## Status

Proposed.

## Decision

Wisk has three canonical learning roles, represented by `SessionType`s:

1. **Experience** — execute real work using the available procedural guidance and record what actually happened.
2. **Wiki** — synthesize multiple experiences into durable knowledge, including comparative evidence when different skill variants were exercised.
3. **Skill** — use durable knowledge and supporting experiences to create, refine, promote, reject, deprecate, or replace procedural guidance.

Skill evaluation is **not a fourth canonical session role**. Evaluation is a workflow that emerges across the three roles:

```text
Skill creates a candidate beside the incumbent
        │
        ▼
Experience exercises incumbent and/or candidate in real work
        │
        ▼
Wiki distinguishes, consolidates, and compares the resulting experiences
        │
        ▼
Skill consumes that synthesis and decides the candidate's next state
        │
        └────► refine / continue experimenting / promote / reject
```

The important unit is therefore not an isolated evaluator session, but the lineage connecting a candidate procedure to the experiences produced under it, the knowledge synthesized from those experiences, and the later skill decision.

## 1. Experience owns observation, not judgment

An Experience session performs useful external work. It may run under the currently active skill or under an experimental candidate. Its responsibility is to preserve truthful episodic evidence about the execution, including which skill/version guided it.

Experience does not decide that the candidate is globally better. A successful run is evidence; it is not promotion.

The existing `Experience.skill_used` and `Experience.skill_version` fields are sufficient for the first implementation when the candidate is represented as an experimental `AgentSkill` version. No new SQL field is required merely to distinguish incumbent from candidate.

## 2. Wiki owns synthesis and comparison

A Wiki session reads experiences and converts episodic evidence into durable knowledge. When a candidate skill is under experiment, the Wiki session should deliberately distinguish evidence generated under the incumbent from evidence generated under the candidate.

The comparison belongs in durable knowledge because the relevant question is not merely whether one benchmark passed, but what repeated executions teach about scope, strengths, regressions, trade-offs, and failure modes.

A `WikiEntry` may therefore synthesize comparative evidence from both variants. Wiki does not promote the skill; it makes the evidence legible for a later Skill session.

## 3. Skill owns intervention and lifecycle decisions

A Skill session changes future procedural behavior. It may:

- create a candidate skill beside an incumbent;
- revise an existing candidate;
- leave a candidate experimental while more evidence accumulates;
- promote a candidate to become the active procedure;
- reject or deprecate a candidate;
- deprecate or replace an incumbent when promotion is justified.

Creating a proposal and accepting it are different moments. A candidate must be executable while the incumbent remains available so Experience sessions can generate comparative evidence.

`SkillProposal` remains useful as a record of the proposed change, motivation, target, and lineage. The executable candidate should be representable as an `AgentSkill` with `status: experimental` and its own version, so normal Experience provenance can identify which procedure was actually used.

## 4. `SkillEvaluation` is an artifact, not a session role

`SkillEvaluation` may remain as an optional explicit snapshot of comparative evidence or a decision record when a consumer needs one. It must not define a separate mandatory stage in the canonical learning cycle, and Wisk must not require a dedicated evaluator SessionType for skill evolution to work.

Consumers may still define specialized reviewer/evaluator sessions for their own workflows. Those are consumer specializations, not a fourth core learning role.

## 5. Canonical SessionTypes and specialization

Wisk should ship canonical parent SessionTypes corresponding to the three roles:

- `session-types/experience`
- `session-types/wiki`
- `session-types/skill`

Consumer repositories should normally extend these parents rather than recreate the learning roles from scratch. Domain-specific execution sessions — software development, newsroom reporting, legal work, research, and others — are specializations of Experience when their primary purpose is to do real work and emit episodic evidence.

Likewise, consumers may refine Wiki and Skill sessions with their own RunSpecs, policies, cadence, and checks.

The existing names `inference`, `wiki-maintainer`, and `skill-evolver` can be migrated or retained as compatibility aliases/subtypes, but the canonical vocabulary is Experience / Wiki / Skill.

## 6. Run checks are role-specific

There is no universal list of substantive checks that all three roles must satisfy.

- Experience checks establish that work and observations are sufficiently evidenced for later learning.
- Wiki checks establish that synthesis is grounded in experiences and does not erase meaningful differences or counterevidence.
- Skill checks establish that a procedural intervention is justified by accumulated knowledge and that its lifecycle action is explicit.

Consumer RunSpecs may add domain checks. Core Wisk should provide the role and lineage semantics, not hard-code legal, software-development, newsroom, or research quality criteria.

## 7. Lineage invariant

Wisk should make the following path inspectable through ordinary OKF links and authored identifiers:

```text
AgentSkill incumbent/candidate
        ↕
SkillProposal
        ↓
Experience(s) with skill_used + skill_version
        ↓
WikiEntry synthesis/comparison
        ↓
Skill decision and resulting AgentSkill state
```

A later Skill session should be able to answer: what evidence justified creating this candidate, what happened when each variant was used, what durable knowledge was synthesized, and why the candidate was promoted, revised, or rejected.

## 8. Consequences for the current runtime

This RFC intentionally does not require a schema migration for the first useful implementation. The current `AgentSkill.status = experimental`, `Experience.skill_used`, `Experience.skill_version`, `WikiEntry.evidence`, and `SkillProposal` concepts can express the cycle.

The immediate implementation should therefore prefer configuration and semantics over new ontology:

1. add the three canonical parent SessionTypes and corresponding RunSpecs/policies as needed;
2. make existing dogfooding session types extend or alias those parents where appropriate;
3. stop presenting the evaluator SessionType as a mandatory fourth learning phase;
4. update architecture documentation to show evaluation as cross-session lineage;
5. add tests ensuring the canonical roles resolve through SessionType inheritance and remain usable through cadence/session selection.

Only add schema fields later if concrete execution shows that the existing lineage cannot answer a necessary question without ambiguity.

## 9. Non-goals

This RFC does not prescribe:

- a fixed A/B allocation algorithm between incumbent and candidate;
- automatic promotion thresholds;
- domain-specific acceptance metrics;
- a mandatory evaluator agent;
- automatic replacement of an incumbent merely because a candidate exists.

Those decisions can evolve from evidence without changing the three-role model.

## 10. Migration principle

Compatibility should not obscure the model. Existing session names may remain temporarily as children/aliases, but new consumers should learn the Experience / Wiki / Skill vocabulary directly.

The migration is successful when a consumer can adopt Wisk by specializing these three roles, and a skill candidate can move from proposal through real-world experience and wiki synthesis to a later skill decision without requiring a fourth orchestration role.

Closes the design question raised in #56.
