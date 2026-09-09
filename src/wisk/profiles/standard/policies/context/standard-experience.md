---
type: ContextPolicy
id: context-policies/standard-experience
title: Standard Experience context (deprecated compatibility alias)
mode: curated
include:
  - skills
  - handoffs
  - run-specs
exclude:
  - wiki
  - work-runs
  - experiences
  - proposals
instructions: "Compatibility policy for pre-0.4 execution SessionTypes. Execute from applicable skills and explicit continuation state; do not inject Wiki synthesis or proposal history into ordinary Work."
---

# Standard Experience context compatibility alias

Keeps old consumer SessionTypes on the same context boundary as Standard Work during the 0.4 RC migration window.
