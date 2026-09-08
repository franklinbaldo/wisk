---
type: ConceptSpecification
concept_type: AgentSkill
description: "Actionable, procedural guidance and policies executed by agents."
---

# Concept: AgentSkill

An `AgentSkill` is a concise, procedural rulebook. It answers: *given what we learned, how should the agent act?*

A skill may also reference a `RunSpec` that turns the skill into a contract-guided execution protocol. The skill describes reusable procedure; the `RunSpec` describes what a well-formed live run must establish, read, evidence and verify.

## Required Frontmatter Fields

- `type`: Must be `"AgentSkill"`
- `id`: Skill identifier (e.g. `skill-develop-feature`)
- `title`: Human-readable skill name
- `version`: Semver or incremental version string (e.g. `"1.0.0"`)
- `status`: Skill lifecycle state (`"active"`, `"deprecated"`, `"experimental"`)

## Optional Frontmatter Fields

- `derived_from`: Links to the `[WikiEntry](../wiki/...)` patterns that motivated this skill or its latest revision
- `tags`: List of domain/tool tags
- `run_spec`: Link to the default `RunSpec` that operationalizes this skill

`derived_from` is the skill's only edge back into the wiki, and it is what makes a
skill auditable: it answers which synthesized knowledge justifies this procedure.
It carries the role of WikiSkill's `PURPOSE.md`, which maps each skill back to the
wiki patterns that inspired its creation or modification.

## Content Structure

The body must be:
- Concise, procedural, step-by-step.
- Free of raw conversation dumps or unverified notes.

An `experimental` AgentSkill may coexist with the active incumbent while Experience sessions gather evidence under each version. Wiki sessions synthesize and compare those experiences; later Skill sessions decide whether to refine, continue experimenting, promote, reject, deprecate, or replace the candidate. `SkillEvaluation` may record an explicit benchmark when useful, but it is not a mandatory fourth stage of the learning cycle.
