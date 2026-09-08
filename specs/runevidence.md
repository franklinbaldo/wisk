---
type: ConceptSpecification
concept_type: RunEvidence
description: "Typed evidence produced or consulted during a live run."
---

# Concept: RunEvidence

A `RunEvidence` is a concrete fact supporting claims about the current state of a run.

## Required Frontmatter Fields

- `type`: `"RunEvidence"`
- `id`: Evidence identifier
- `run`: Link to the `LoopRun`
- `kind`: Evidence category such as `test_red`, `test_green`, `ci`, `runtime`, `diff`, `source`, `issue`, `pr`, `review`, `benchmark`, or `okf`
- `reference`: Stable locator for the evidence
- `summary`: What the evidence demonstrates

## Optional Frontmatter Fields

- `goal`: Link to the `RunGoal` supported by this evidence
- `decision`: Link to the `RunDecision` this evidence bears on
- `observed_at`: ISO-8601 timestamp

## Semantics

Evidence makes run progress auditable. Domain RunSpecs may require specific evidence kinds before particular outcomes are coherent.
