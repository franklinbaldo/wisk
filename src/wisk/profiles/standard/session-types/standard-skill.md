---
type: SessionType
id: session-types/standard-skill
title: Standard Skill
purpose: "Evolve reusable procedure from durable Wiki knowledge and supporting Experience evidence."
run_spec: run-specs/skill
extends: session-types/skill
context_policy: context-policies/standard-skill
cadence_policy: cadence-policies/standard-skill
nudges:
  - "Keep a candidate experimental while comparative evidence is still accumulating."
  - "Change permanent procedure only when the accumulated evidence justifies the maintenance cost."
---

# Standard Skill

Default consumer skill-evolution specialization. Wiki runs at a higher priority, so when both learning thresholds are reached the Skill session sees fresh synthesis on the following invocation.
