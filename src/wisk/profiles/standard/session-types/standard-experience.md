---
type: SessionType
id: session-types/standard-experience
title: Standard Experience
purpose: "Perform useful work in the consumer repository and preserve reusable episodic evidence."
run_spec: run-specs/experience
extends: session-types/experience
context_policy: context-policies/standard-experience
cadence_policy: cadence-policies/standard-experience
nudges:
  - "Prefer useful repository work over producing Wisk metadata for its own sake."
  - "A no-useful-change outcome is valid when modification would create churn rather than value."
---

# Standard Experience

Default consumer specialization. Repositories can add a local SessionType that extends this one and selects a domain-specific RunSpec.
