---
type: ConceptSpecification
concept_type: RunDecision
description: "A consequential choice made during a live run, with rationale and linkage to the goal it advances."
---

# Concept: RunDecision

A `RunDecision` records a meaningful choice that changes how the run proceeds.

## Required Frontmatter Fields

- `type`: `"RunDecision"`
- `id`: Decision identifier
- `run`: Link to the `LoopRun`
- `question`: Decision point or problem being resolved
- `decision`: Chosen direction
- `rationale`: Why this choice is appropriate given current evidence

## Optional Frontmatter Fields

- `goal`: Link to the `RunGoal` advanced by the decision
- `alternatives`: Other options materially considered

## Semantics

The purpose is not to log every thought. Record decisions that affect architecture, scope, interpretation, prioritization, validation, or the next state of the run.

A decision carries no link to evidence in either direction. It is recorded before
the evidence supporting it exists, and run components are append-only, so no such
edge can be written honestly at either end. Evidence links to its `run` and `goal`;
`RunCheck.evidence` ties a verification to the concrete fact it rests on. Causal
analysis across those records is Wiki work, not raw-layer bookkeeping.
