---
type: ConceptSpecification
concept_type: SkillProposal
description: "Proposed candidate version or modification for an AgentSkill."
---

# Concept: SkillProposal

A `SkillProposal` represents an explicit proposal to create, modify, or deprecate an `AgentSkill`.

The proposal is the change record and rationale; it is not itself required to be the executable procedure. When a proposed procedure needs real-world comparison, the candidate should be materialized as an `AgentSkill` with `status: experimental` and its own version while the incumbent remains available. Experience can then identify the procedure actually used through `skill_used` and `skill_version` without a special evaluation runtime.

## Required Frontmatter Fields

- `type`: Must be `"SkillProposal"`
- `id`: Proposal identifier (e.g. `prop-2026-09-02-01`)
- `title`: Short title of the proposed change
- `target_skill`: Link or identifier to the target `AgentSkill`
- `status`: Proposal status (`"draft"`, `"evaluating"`, `"accepted"`, `"rejected"`)

## Optional Frontmatter Fields

- `motivation`: Summary of the reason for the proposal
- `based_on`: Links to motivating `[WikiEntry](../wiki/...)` or `[Experience](../experiences/...)`
- `run`: Link to the `LoopRun` that produced this proposal

## Content Structure

The body should present:
1. **Current Procedure vs Proposed Procedure**: Diff or before/after comparison.
2. **Rationale**: Evidence justifying the change.
3. **Candidate identity when executable**: Identify the experimental `AgentSkill` id/version in the body so the proposal and execution lineage remain legible.

Creating the proposal does not accept it. Later Experience and Wiki sessions gather and synthesize evidence; a later Skill session decides whether the candidate should be refined, promoted, rejected, or left experimental.
