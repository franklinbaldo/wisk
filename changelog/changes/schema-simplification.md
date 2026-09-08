---
type: Changelog
version: 0.4.0
date: 2026-09-08
---

# Schema simplification: one source of truth per link

Run components already carry a `run` back-reference, and the runtime derives every
component list from that reference. The parallel lists stored on `LoopRun` were a
second, drift-prone copy of the same graph, so they are gone.

- `LoopRun` drops `readings`, `goals`, `decisions`, `evidence`, `checks`, `outcome`,
  `skills_consulted`, `experiences_recorded`, and `proposals_generated`. `status`
  (`scaffold` / `in_progress` / `closed`) now reports run progress on its own, and
  the outcome guard reads the run's `RunOutcome` records instead of a stored pointer;
- `RunOutcome` drops `goals_advanced` and `experiences_recorded`, which `RunGoal.status`
  and `Experience.run` already carry. It keeps `evidence` and `checks`: those are a
  selection of what is decisive for the close, not an inventory of what belongs to the
  run, and the difference is real when a run holds a failed early check and a later
  passing one;
- the decision/evidence link now lives on `RunEvidence.decision`, and `RunDecision.evidence`
  is gone. A decision is recorded before its supporting evidence exists and components are
  append-only, so only this direction is writable;
- `SkillProposal` gains `run`, the back-reference that replaces the dropped
  `LoopRun.proposals_generated` on the side that owns the link. `AgentSkill` keeps
  `derived_from`: it is the skill's only edge back into the wiki, unexercised so far
  rather than dead;
- `RunSpec` drops the unused `allowed_entry_states`;
- `LoopRun.timestamp` and `RunEvidence.observed_at` become `TIMESTAMPTZ`, matching
  `Experience.timestamp`.

This is a breaking schema change: a consumer bundle carrying the removed frontmatter
keys fails normative OKF validation until they are dropped.
