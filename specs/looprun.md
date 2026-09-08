---
type: ConceptSpecification
concept_type: LoopRun
description: "Live execution instance scaffolded from a RunSpec and progressively satisfied through typed evidence and checks."
---

# Concept: LoopRun

A `LoopRun` is the live state of one agent execution round.

It exists before substantive work begins, starts intentionally incomplete, and accumulates typed readings, goals, decisions, evidence, checks and an outcome as the session progresses.

The applicable `RunSpec` defines what a well-formed run of this class requires. The `SessionType` records what kind of session created the run and supplies its purpose, inherited nudges, and default RunSpec selection. Repeated `okf-parser` validation provides operational feedback about missing or inconsistent state.

## Required Frontmatter Fields

- `type`: `"LoopRun"`
- `id`: Run identifier
- `title`: Short summary of the run
- `timestamp`: ISO-8601 start timestamp
- `status`: `"scaffold"`, `"in_progress"`, or `"closed"`
- `run_spec`: Link to the governing `RunSpec`
- `session_type`: Link to the effective `SessionType`
- `task`: Task or session intent

## Pinned RunSpec provenance

New LoopRuns freeze the complete RunSpec frontmatter that governed the run at creation time:

- `run_spec_version`: authored version of the governing RunSpec;
- `run_spec_digest`: `sha256:` digest of the canonical snapshot;
- `run_spec_snapshot`: deterministic JSON serialization of the complete RunSpec frontmatter.

`check_run()` validates a pinned run against this snapshot rather than the mutable current RunSpec. The digest and version make tampering or accidental divergence explicit. Legacy LoopRuns that predate pinning may omit these fields and continue to resolve their current `run_spec` reference as a compatibility fallback.

## Run components

A LoopRun stores no lists of its own components. Every `RunReading`, `RunGoal`, `RunDecision`, `RunEvidence`, `RunCheck`, `RunOutcome`, and `Experience` carries a `run` link back to the LoopRun, and the runtime derives a run's components from those links.

The single source of truth is the child record. `status` alone reports how far the run has progressed: `scaffold` before any component exists, `in_progress` while components accumulate, `closed` once a `RunOutcome` has been written for the run.

## Operational semantics

A new run should be created from a scaffold before meaningful execution work. It is normal for that scaffold to fail completion validation initially.

The agent then cycles through:

```text
validate live run
-> inspect unsatisfied requirements
-> perform the next useful action
-> record typed state/evidence
-> validate again
```

Closing is stronger than merely filling the RunSpec fields. Every RunGoal owned by the run must have a terminal destination before `RunOutcome` may close it:

- `achieved`: the current run resolved the intent;
- `carried_forward`: a Handoff created by this run explicitly lists the goal and transfers it onward.

Goals left `planned`, `active`, or `advanced` keep the run incomplete. A partial outcome also requires a Handoff to exist before the close is written. Archived Handoffs remain valid provenance for the historical source run.

The final run is both an auditable record of what happened and a structured handoff describing the state reached and the next natural move.
