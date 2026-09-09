---
type: ConceptSpecification
concept_type: AgentSkill
description: "Actionable, procedural guidance and policies executed by agents."
---

# Concept: AgentSkill

An `AgentSkill` is a concise, procedural rulebook. It answers: *given what we learned, how should the agent act?*

A skill may reference a `RunSpec` that turns the procedure into a contract-guided execution protocol. The skill describes reusable procedure; the RunSpec describes what a well-formed run must establish, read, evidence and verify.

## Required Frontmatter Fields

- `type`: `"AgentSkill"`
- `id`: Skill identifier
- `title`: Human-readable skill name
- `version`: Semver or incremental version string
- `status`: `"active"`, `"deprecated"`, or `"experimental"`

## Optional Frontmatter Fields

- `derived_from`: Links to the `WikiEntry` patterns that motivated this skill or its latest revision
- `tags`: Domain/tool tags
- `run_spec`: Default RunSpec that operationalizes this skill

`derived_from` is the skill's edge back into the Wiki and makes the procedure auditable: it answers which synthesized knowledge justified the intervention. It carries the role of WikiSkill's `PURPOSE.md`, which maps a skill to the Wiki patterns that inspired its creation or modification.

## Content Structure

The body must be concise, procedural, step-by-step, and free of raw conversation dumps or unverified notes.

An `experimental` AgentSkill may coexist with the active incumbent while Work sessions exercise each version. `RunSkillUse` records the exact version that actually guided each Work run. Wiki sessions synthesize and compare those raw traces; later Skill sessions decide whether to refine, continue experimenting, promote, reject, deprecate, or replace the candidate. `SkillEvaluation` may record a detailed benchmark when useful, but it is not a mandatory fourth canonical session role.
