---
type: Changelog
version: 0.2.3
date: 2026-09-05
---

# Experience Recording joins contract-guided execution

- restores `preview_experience()` and `record_experience()` on top of the RunSpec/LoopRun runtime;
- validates every persisted Experience with the normative OKF gate and rolls back invalid writes;
- exposes `wisk experience preview|record` plus FastMCP preview/write tools;
- lets an Experience reference the `LoopRun` that produced it, preserving execution-to-learning provenance;
- preserves the original causal TDD history from PR #23 while reanchoring the implementation on the current runtime.
