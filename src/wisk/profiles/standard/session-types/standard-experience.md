---
type: SessionType
id: session-types/standard-experience
title: Standard Experience (deprecated compatibility alias)
purpose: "Preserve pre-0.4 consumer inheritance while applying the canonical Work execution semantics."
run_spec: run-specs/experience
extends: session-types/experience
context_policy: context-policies/standard-experience
cadence_policy: cadence-policies/standard-experience
nudges:
  - "Deprecated in 0.4: new consumer execution roles should extend session-types/standard-work."
  - "Treat the LoopRun and its typed Run* children as the raw execution trace; do not create a redundant Experience summary as part of ordinary Work."
  - "Leave Wiki synthesis and Skill intervention to their later roles."
---

# Standard Experience compatibility alias

This managed SessionType remains during the 0.4 RC so existing consumer SessionTypes that extend `session-types/standard-experience` continue to resolve. It inherits the canonical Work role through `session-types/experience`.

New consumers should use `session-types/standard-work`.
