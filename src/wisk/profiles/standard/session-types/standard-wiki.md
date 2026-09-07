---
type: SessionType
id: session-types/standard-wiki
title: Standard Wiki
purpose: "Synthesize accumulated Experience into durable knowledge when enough evidence exists."
run_spec: run-specs/wiki
extends: session-types/wiki
context_policy: context-policies/standard-wiki
cadence_policy: cadence-policies/standard-wiki
nudges:
  - "Prefer updating existing durable knowledge over creating duplicate entries."
  - "Preserve meaningful differences between skill variants, counterexamples, and uncertainty."
---

# Standard Wiki

Default consumer synthesis specialization. It is threshold-driven rather than scheduled merely to create periodic documentation.
