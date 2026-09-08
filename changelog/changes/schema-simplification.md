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
- `RunOutcome` drops `goals_advanced`, `experiences_recorded`, `evidence`, and `checks`.
  The outcome stays small — state, summary, continuation — and what makes a close
  legitimate moves into the runtime instead;
- **a `required_check_kind` is now satisfied only when the run's standing check of that
  kind passes.** Presence of a check was being read as verification: `check_run()` matched
  on `kind` and never looked at `status`, so a run could close on a check that failed.
  `RunCheck` gains `observed_at`, the standing check of a kind is the latest one recorded,
  and `fail` or `inconclusive` keeps the run open. This is why the outcome needs no list
  of the checks that sustain it;
- the decision/evidence link is gone from both sides. A decision is recorded before its
  supporting evidence exists and components are append-only, so neither end can be written
  honestly. `RunCheck.evidence` still ties a verification to the fact it rests on, and
  causal analysis across records is Wiki work;
- `SkillProposal` gains `run`, the back-reference that replaces the dropped
  `LoopRun.proposals_generated` on the side that owns the link. `AgentSkill` keeps
  `derived_from`: it is the skill's only edge back into the wiki, unexercised so far
  rather than dead;
- `RunSpec` drops the unused `allowed_entry_states`;
- `SkillProposal` gets a typed gating contract and its own schema: `target_version`,
  `candidate_skill`, `candidate_version`, `validation`, `decided_at`, and
  `decision_rationale`. A rejected proposal is kept, not deleted — it is what stops a
  later Skill session from retrying a change that already failed;
- `LoopRun.timestamp`, `RunEvidence.observed_at`, and `RunCheck.observed_at` are
  `TIMESTAMPTZ`, matching `Experience.timestamp`.

This is a breaking schema change: a consumer bundle carrying the removed frontmatter
keys fails normative OKF validation until they are dropped. `wisk migrate` reports what
it would remove from a bundle, and `wisk migrate --apply` removes it.
