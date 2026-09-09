---
type: RunSpec
id: run-specs/wiki
title: Wiki synthesis run
version: "1.1.0"
status: experimental
required_reading_kinds:
  - work-runs
  - wiki
required_goal_kinds:
  - consolidate-knowledge
required_evidence_kinds:
  - consolidation
required_check_kinds:
  - grounding
allowed_result_states:
  - updated
  - no-change
  - partial
  - blocked
completion_notes: "Synthesize durable knowledge from a corpus of Work traces; preserve meaningful differences, counterevidence, scope and skill-version provenance rather than collapsing them."
---

# Wiki RunSpec

The canonical synthesis contract. `grounding` asks whether WikiEntry claims are traceable to closed Work `LoopRun` evidence and whether meaningful counterevidence or variant differences were preserved.

Operational handoffs are deliberately absent from the contract: resolving unfinished external work is a Work responsibility, not a reason to run Wiki synthesis.
