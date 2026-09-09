---
type: RunSpec
id: run-specs/experience
title: Experience run (deprecated compatibility alias)
version: "1.1.0"
status: experimental
parent_spec: run-specs/work
allowed_result_states:
  - success
  - partial
  - blocked
  - no-useful-change
completion_notes: "Compatibility bridge for pre-0.4 consumers. New execution sessions should use run-specs/work."
---

# Experience RunSpec compatibility alias

This RunSpec inherits the canonical Work execution contract during the 0.4 RC migration window. It exists so old authored references remain resolvable; it is not a second execution model.
