---
type: RunGoal
id: run-goals/20260905-contract-runtime
run: runs/20260905-contract-guided-runtime
kind: project-advance
goal: "Make contract-guided execution a usable, typed, self-hosted Wisk runtime rather than only an architectural proposal."
rationale: "The pivot is useful only if agents can start/check real runs and every run component has a first-class OKF contract."
success_signal: "start/check is merged, all run types export from declared schemas, and Wisk persists a real live run governed by its own RunSpec."
status: achieved
---

# Project advance goal

The success signal was reached: executable start/check is merged, every run component has a declared exportable schema, and Wisk has persisted and completed a real run governed by its own RunSpec.
