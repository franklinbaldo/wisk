---
type: ConceptSpecification
concept_type: RunOutcome
description: "The coherent state reached at the end of the current run and its natural continuation."
---

# Concept: RunOutcome

A `RunOutcome` closes the current execution round without requiring that the larger task or feature be finished.

## Required Frontmatter Fields

- `type`: `"RunOutcome"`
- `id`: Outcome identifier
- `run`: Link to the `LoopRun`
- `result_state`: Domain state reached by this run
- `work_status`: Whether the material work owned by this run is `complete` or `partial`
- `summary`: What materially changed
- `next_move`: Natural continuation available to a future run

## Optional Frontmatter Fields

- `evidence`: Links to the `RunEvidence` that is decisive for this result
- `checks`: Links to the `RunCheck` records that establish this close

These are a selection, not an inventory. "Belongs to the run" is already carried
by each component's own `run` link; these fields answer a different question,
namely which evidence and which checks actually support *this* close. The
distinction matters because a run may hold a `RunCheck` that failed early and a
later one that passed, and only the second sustains the outcome.

The outcome carries no `goals_advanced` or `experiences_recorded`: a `RunGoal`
reaching `achieved` or `carried_forward` and an `Experience` naming its `run`
already say that, with no second copy to keep in sync.

## Semantics

`result_state` remains domain-specific: RED, GREEN, review-ready, merged, blocked, published, investigated, or another state allowed by the applicable `RunSpec`.

`work_status` answers a separate operational question. `complete` means the work intentionally owned by this round has been closed. `partial` means material work remains and must be represented by an active `Handoff` so that a later `LoopRun` can resume it explicitly.
