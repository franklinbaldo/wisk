---
type: RunSpec
id: run-specs/work
title: Work run
version: "1.0.0"
status: experimental
required_reading_kinds:
  - active-handoffs
  - active-skills
required_goal_kinds:
  - task-advance
required_evidence_kinds:
  - execution
required_check_kinds:
  - verification
allowed_result_states:
  - success
  - partial
  - blocked
  - no-useful-change
completion_notes: "Do useful work when available, verify the observed result, and preserve a truthful raw execution trace including exact skill/version provenance when skills guided the work."
---

# Work RunSpec

The canonical execution contract. `verification` asks whether the claimed observed effect is supported by execution evidence. It does not decide whether a skill should be promoted globally.

`RunObservation` and `RunSkillUse` are not universally required because some Work runs have no notable friction and some tasks use no AgentSkill. When they are relevant, they are first-class children of the Work LoopRun rather than a separate Experience summary.
