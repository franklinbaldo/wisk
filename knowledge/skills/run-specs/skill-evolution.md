---
type: RunSpec
id: run-specs/skill-evolution
title: Skill evolution run
version: "1.1.0"
status: experimental
parent_spec: run-specs/skill
required_evidence_kinds:
  - proposal
required_check_kinds:
  - evidence
allowed_result_states:
  - proposed
  - refined
  - promoted
  - rejected
  - no-change
  - partial
  - blocked
completion_notes: "Produce one evidence-linked procedural intervention only when persistent Wiki knowledge and selected Work traces justify it, preserving prior proposal outcomes."
---

# Skill evolution RunSpec

Wisk dogfood specialization of the canonical Skill contract. It inherits Wiki, Work-trace, active-skill and proposal-history readings and adds proposal/evidence bookkeeping for repository skill changes.
