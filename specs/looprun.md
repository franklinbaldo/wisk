---
type: ConceptSpecification
concept_type: LoopRun
description: "Persisted execution instance whose typed child graph is Wisk's Raw Layer for real Work sessions."
---

# Concept: LoopRun

A `LoopRun` is the persisted state of one agent execution round. For a Work SessionType, the closed LoopRun plus its typed child records is Wisk's repository-resident Raw Layer: the execution trace that later Wiki sessions can study without relying on provider chat history.

It exists before substantive work begins, starts intentionally incomplete, and accumulates typed readings, goals, decisions, evidence, checks, observations, skill-use provenance and an outcome as the session progresses.

The applicable `RunSpec` defines what a well-formed run requires. `SessionType` records the cognitive role exercised by the run and supplies its purpose, inherited nudges, policies, and default RunSpec selection.

## Required Frontmatter Fields

- `type`: `"LoopRun"`
- `id`: Run identifier
- `title`: Short summary of the run
- `started_at`: ISO-8601 execution start timestamp
- `status`: `"scaffold"`, `"in_progress"`, or `"closed"`
- `run_spec`: Link to the governing `RunSpec`
- `session_type`: Link to the effective `SessionType`
- `task`: Task or session intent

## Optional Frontmatter Fields

- `finished_at`: ISO-8601 execution finish timestamp, written when the run closes
- `timestamp`: Legacy pre-0.4 start timestamp retained for read/migration compatibility
- `resumed_handoff`: Handoff consumed by this run, when any

Duration is derived from `started_at` and `finished_at`; an agent must not estimate it.

## Pinned RunSpec provenance

New LoopRuns freeze the complete RunSpec frontmatter that governed the run at creation time:

- `run_spec_version`: authored version of the governing RunSpec;
- `run_spec_digest`: `sha256:` digest of the canonical snapshot;
- `run_spec_snapshot`: deterministic JSON serialization of the complete RunSpec frontmatter.

`check_run()` validates a pinned run against this snapshot rather than the mutable current RunSpec. Legacy LoopRuns that predate pinning may omit these fields and continue to resolve their current `run_spec` reference as a compatibility fallback.

## Raw run components

A LoopRun stores no lists of its own components. Every `RunReading`, `RunGoal`, `RunDecision`, `RunEvidence`, `RunCheck`, `RunObservation`, `RunSkillUse`, and `RunOutcome` carries a `run` link back to the LoopRun, and the runtime derives membership from those links.

The single source of truth for membership is the child record. Semantic relationships that mean more than membership remain explicit, such as `RunCheck.evidence`, `WikiEntry.evidence`, `AgentSkill.derived_from`, and SkillProposal lineage/gating history.

`status` reports how far the run has progressed: `scaffold` before any component exists, `in_progress` while components accumulate, and `closed` once a `RunOutcome` has been written and `finished_at` recorded.

A separate canonical `Experience` document is not required to restate a Work run. Old Experience documents remain readable during the 0.4 RC migration window.

## Operational semantics

A new run is created from a scaffold before meaningful execution work. It is normal for that scaffold to fail completion validation initially.

The agent cycles through:

```text
validate live run
-> inspect unsatisfied requirements
-> perform the next useful action
-> record typed state/evidence/observations
-> validate again
```

Closing is stronger than merely filling RunSpec fields. Every RunGoal owned by the run must have a terminal destination before `RunOutcome` may close it:

- `achieved`: the current run resolved the intent;
- `carried_forward`: a Handoff created by this run explicitly lists the goal and transfers it onward.

Goals left `planned`, `active`, or `advanced` keep the run incomplete. A partial outcome also requires a Handoff to exist before the close is written. Required checks are satisfied only by the standing/latest passing check of each required kind.

The final Work run is both an auditable record of what happened and raw evidence for future synthesis. Its `next_move` is research/continuation material, not an instruction that later agents must obey.
