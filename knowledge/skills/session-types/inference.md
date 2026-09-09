---
type: SessionType
id: session-types/inference
title: Inference / work execution (compatibility alias)
purpose: "Backward-compatible paper-oriented name for the canonical Work role."
run_spec: run-specs/inference
extends: session-types/work
context_policy: context-policies/inference
access_policy: access-policies/development
cadence_policy: cadence-policies/inference
nudges:
  - "Use applicable skills as operating procedure and focus on the task in front of the session."
  - "Persist the Work LoopRun trace instead of relying on provider-local session memory."
---

# Inference session

Backward-compatible WikiSkill-paper vocabulary for a Work session. New consumers should normally extend `session-types/work` or `session-types/standard-work`.
