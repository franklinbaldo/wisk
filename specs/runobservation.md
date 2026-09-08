---
type: ConceptSpecification
concept_type: RunObservation
description: "Structured execution-adjacent observation captured while a Work run still has hot context."
---

# Concept: RunObservation

A `RunObservation` preserves locally important execution facts that are useful to later synthesis but are not themselves a goal, formal decision, evidence item, or verification check.

The core vocabulary is deliberately small: `friction`, `surprise`, `near_miss`, `workaround`, `opportunity`, and `skill_feedback`. Consumer bundles may use additional domain-specific kinds.

## Required Frontmatter Fields

- `type`: `"RunObservation"`
- `id`: Stable observation identifier
- `run`: Link to the owning `LoopRun`
- `kind`: Observation category
- `summary`: Concise factual description of what happened
- `impact`: `low`, `medium`, or `high`
- `observed_at`: ISO-8601 timestamp for when the observation was recorded

## Optional Frontmatter Fields

- `skill_use`: Link to a `RunSkillUse` when the observation is specifically about procedural guidance

## Semantics

RunObservation is raw execution texture, not durable synthesis. A Worker should record what hurt, helped, surprised it, nearly went wrong, or remained worth investigating. A later Wiki Maintainer decides whether repeated observations justify a durable `WikiEntry`.

The record must not contain private chain-of-thought. Preserve observable actions, outputs, explicit assessments, and other safe execution facts.
