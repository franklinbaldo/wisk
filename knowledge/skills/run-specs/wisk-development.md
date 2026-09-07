---
type: RunSpec
id: run-specs/wisk-development
title: Wisk development run
version: "1.1.0"
status: experimental
required_reading_kinds:
  - repository-guide
  - open-issues
  - open-prs
  - okf-knowledge
  - recent-runs
  - active-handoffs
required_goal_kinds:
  - project-advance
required_evidence_kinds:
  - change
  - verification
required_check_kinds:
  - okf
  - tests
allowed_entry_states:
  - new
  - active
  - review
  - blocked
allowed_result_states:
  - red
  - green
  - review
  - merged
  - blocked
completion_notes: "A development run should leave typed evidence of what changed, how it was verified, and what continuation is now natural. Partial work must leave an active Handoff."
---

# Wisk development run

This RunSpec dogfoods contract-guided execution inside Wisk itself.

A session begins by creating a `LoopRun` scaffold before substantive work. The run records repository/context readings, including active handoffs from earlier sessions, one or more observable goals, consequential decisions, evidence, checks, and a coherent outcome.

The run is validated repeatedly with `okf-parser`. Missing required state is treated as guidance about what the session should establish next.

When the session declares `work_status: partial`, it emits a `Handoff` with enough state and references for a future `LoopRun` to resume the work. A later run records the handoff reading and archives the handoff when it actually continues that work.

This spec is intentionally evolvable. Evidence from real development runs may justify changing its required reading, goal, evidence, check, or state categories through the normal Wisk learning lifecycle.
