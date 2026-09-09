---
type: Changelog
version: 0.4.0rc1
date: 2026-09-08
---

# 0.4 RC: schema simplification and learning-model pivot

This pre-release begins the 0.4 architecture migration described by RFC 0007. It keeps the one-source-of-truth schema cleanup from PR #70, but deliberately ships as an RC while the canonical Work → Wiki → Skill → Work learning loop is dogfooded in a real consumer before stable 0.4.0.

Run components already carry a `run` back-reference, and the runtime derives every component list from that reference. The parallel lists stored on `LoopRun` were a second, drift-prone copy of the same graph, so they are gone.

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
  `TIMESTAMPTZ`, matching the previous Experience timestamp contract.

RFC 0007 deliberately expands the 0.4 target beyond this first patch: the RC will migrate the canonical execution role from Experience to Work, treat Work LoopRun traces as the Raw Layer, add run observations and explicit skill/version provenance, separate Worker/Wiki/Skill context policies, and dogfood a complete skill-evolution cycle before promotion to stable `0.4.0`.

This is a breaking schema change: a consumer bundle carrying the removed frontmatter
keys fails normative OKF validation until they are dropped. `wisk migrate` reports what
it would remove from a bundle, and `wisk migrate --apply` removes it.

## Correctness fixes found while validating the RC

- **the standing check is now chosen by instant, not by timestamp text.** `observed_at`
  values were compared as strings, so `2026-09-01T12:00:00-03:00` sorted before
  `2026-09-01T14:00:00Z` although it is the later instant, and the superseded check could
  win. The values are parsed before they are compared;
- **an unorderable check can no longer grant closure.** A check recorded without
  `observed_at`, or with an unparseable one, sorted as the oldest of its kind, so a later
  `fail` was masked by an earlier `pass` and the required kind counted as satisfied —
  the exact hole this RC set out to close. When the records of one kind cannot be
  ordered, a non-passing check now stands and the run stays open;
- `record_run_check` and `record_run_evidence` default `observed_at` to the current
  instant, as the Work path already did, so nothing Wisk writes is unorderable;
- **`wisk migrate --apply` no longer corrupts a multi-line flow collection.** Dropping a
  removed key whose value spanned several lines as `[` … `]` left the closing bracket
  behind, and the applied frontmatter no longer parsed. Brackets inside quoted scalars
  are not counted as collection delimiters;
- **`wisk migrate` no longer retargets an archived Handoff.** Retargeting exists so an
  *active* handoff is not stranded on a session type that is no longer selectable. An
  archived handoff records which session type actually continued the work, and rewriting
  it would falsify that history.
- **`wisk migrate` now finds the bundle a consumer actually has.** It defaulted to a
  literal `knowledge/` directory while every other command resolves the managed
  `.wisk/knowledge` through `resolve_knowledge_path`, so a bare `wisk migrate` in a real
  consumer failed with `Not a directory` — the opaque failure the migration path exists
  to avoid.

