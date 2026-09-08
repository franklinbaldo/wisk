---
type: SessionType
id: session-types/standard-experience
title: Standard Experience
purpose: "Perform useful work in the consumer repository and preserve truthful raw episodic evidence about what actually happened."
run_spec: run-specs/experience
extends: session-types/experience
context_policy: context-policies/standard-experience
cadence_policy: cadence-policies/standard-experience
nudges:
  - "Prefer useful repository work over producing Wisk metadata for its own sake."
  - "Record Experience as raw episodic evidence; do not synthesize it into WikiEntry or evolve AgentSkill in an Experience session. Wiki owns synthesis and Skill owns procedural change."
  - "A no-useful-change outcome is valid when modification would create churn rather than value."
---

# Standard Experience

Default consumer specialization. Repositories can add a local SessionType that extends this one and selects a domain-specific RunSpec.

Experience owns observation, not synthesis or skill evolution. Preserve what happened faithfully enough that later Wiki sessions can consolidate multiple Experiences and later Skill sessions can decide whether procedural guidance should change.
