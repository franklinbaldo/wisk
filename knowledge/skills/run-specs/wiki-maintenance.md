---
type: RunSpec
id: run-specs/wiki-maintenance
title: Wiki maintenance run
version: "1.1.0"
status: experimental
parent_spec: run-specs/wiki
required_check_kinds:
  - okf
allowed_result_states:
  - updated
  - no-change
  - partial
  - blocked
completion_notes: "Consolidate useful Work trace evidence into WikiEntry knowledge and validate the resulting OKF state without performing operational handoff work."
---

# Wiki maintenance RunSpec

Wisk dogfood specialization of the canonical Wiki contract. It inherits Work-corpus grounding and adds an OKF integrity check for repository knowledge changes.
