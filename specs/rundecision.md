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

A decision is recorded before the evidence that supports it exists, and run
components are append-only, so the link lives on `RunEvidence.decision`: later
evidence declares which decision it bears on.
