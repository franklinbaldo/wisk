---
type: Changelog
version: 0.3.2
date: 2026-09-08
---

# Schema simplification: one source of truth per link

Run components already carry a `run` back-reference, and the runtime derives every
component list from that reference. The parallel lists stored on `LoopRun` and
`RunOutcome` were a second, drift-prone copy of the same graph, so they are gone.

- `LoopRun` drops `readings`, `goals`, `decisions`, `evidence`, `checks`, `outcome`,
  `skills_consulted`, `experiences_recorded`, and `proposals_generated`. `status`
  (`scaffold` / `in_progress` / `closed`) now reports run progress on its own, and the
  outcome guard reads the run's `RunOutcome` records instead of a stored pointer;
- `RunOutcome` drops `goals_advanced`, `evidence`, `checks`, and `experiences_recorded`;
- `RunEvidence` drops `decision`, keeping the single `RunDecision.evidence` direction;
- `RunSpec` drops the unused `allowed_entry_states`;
- `SkillProposal` gains `run`, the back-reference that replaces the dropped
  `LoopRun.proposals_generated` on the side that owns the link. `AgentSkill` keeps
  `derived_from`: it is the skill's only edge back into the wiki, unexercised so far
  rather than dead;
- `LoopRun.timestamp` and `RunEvidence.observed_at` become `TIMESTAMPTZ`, matching
  `Experience.timestamp`;
- `wisk run evidence` and `wisk run outcome`, and their MCP equivalents, lose the
  parameters for the removed fields.
