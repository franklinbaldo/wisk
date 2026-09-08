---
type: SessionType
id: session-types/development
title: Wisk development session
purpose: "Advance the repository through implementation and verification while preserving a raw Work trace for later learning."
run_spec: run-specs/wisk-development
extends: session-types/work
context_policy: context-policies/development
access_policy: access-policies/development
output_policy: output-policies/default
cadence_policy: cadence-policies/development
nudges:
  - "Maintain the LoopRun as auditable execution state and persist unfinished work through typed continuation state rather than hidden context."
  - "Prefer a concrete repository advance over commentary about possible work."
  - "Use the repository's issues, PRs, checks, handoffs, and OKF state as first-class execution context."
  - "Record execution observations and skill provenance when they are useful to later Wiki synthesis."
---

# Development session

Wisk's dogfood development specialization of the canonical Work role. It carries the output policy that the former role-neutral `session-types/base` supplied without making the canonical Work role depend on Wisk-specific dogfood state.
