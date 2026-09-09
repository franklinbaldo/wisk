---
type: ConceptSpecification
concept_type: RunSkillUse
description: "Objective provenance for the exact AgentSkill version that guided one Work run."
---

# Concept: RunSkillUse

A `RunSkillUse` records which executable procedure actually guided a Work run. It replaces the provenance role previously carried by `Experience.skill_used` and `Experience.skill_version` without requiring a separate Experience artifact.

## Required Frontmatter Fields

- `type`: `"RunSkillUse"`
- `id`: Stable skill-use identifier
- `run`: Link to the owning `LoopRun`
- `skill`: Link to the `AgentSkill`
- `skill_version`: Exact version exercised by the run
- `skill_status`: Lifecycle state when exercised: `active` or `experimental`
- `observed_at`: ISO-8601 timestamp for when the use was recorded

## Optional Frontmatter Fields

- `notes`: Applicability or usage notes that do not amount to global evaluation

## Semantics

This record is provenance first. A later Wiki or Skill session must be able to query all Work runs that exercised a particular skill version and compare their goals, outcomes, checks, and observations.

Local helpful/harmful assessment may be captured in `RunObservation(kind: skill_feedback)` and linked to this record. One successful or failing use does not itself promote or reject a skill.
