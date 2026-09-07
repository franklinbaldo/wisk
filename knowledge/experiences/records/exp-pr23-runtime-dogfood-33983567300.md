---
type: "Experience"
id: "exp-pr23-runtime-dogfood-33983567300"
title: "Experience Recording dogfood via Wisk runtime"
timestamp: "2026-09-05T18:17:58.979991Z"
status: "success"
task: "Revive PR #23 Experience Recording on the contract-guided runtime"
context: "Generated inside GitHub Actions by Wisk.record_experience; workflow run 33983567300."
run: "runs/20260905-contract-guided-runtime"
---

# Experience Recording runtime dogfood

## Context & Intent
Prove that the revived Experience Recording feature can generate its own OKF learning artifact.

## Action & Observed Output
GitHub Actions invoked Wisk.record_experience() against a copy of the repository knowledge bundle and the runtime accepted the write.

## Findings
Experience Recording now closes execution-to-learning provenance by linking the generated Experience to its producing LoopRun.
