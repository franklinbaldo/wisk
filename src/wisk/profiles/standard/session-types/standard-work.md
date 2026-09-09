---
type: SessionType
id: session-types/standard-work
title: Standard Work
purpose: "Perform the best useful work available in the consumer repository and persist the raw execution trace needed for later learning."
run_spec: run-specs/work
extends: session-types/work
context_policy: context-policies/standard-work
cadence_policy: cadence-policies/standard-work
nudges:
  - "Prefer useful repository work over producing Wisk metadata for its own sake."
  - "Capture relevant execution observations while context is hot; leave cross-run synthesis to Wiki."
  - "Record the exact skill/version actually used when procedural guidance materially guides the run."
  - "A no-useful-change outcome is valid when modification would create churn rather than value."
---

# Standard Work

Default consumer specialization of the canonical Worker role. Repositories can add local SessionTypes that extend this one and select domain-specific RunSpecs or policies.
