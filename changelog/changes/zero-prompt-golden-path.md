---
type: Changelog
version: 0.3.0
date: 2026-09-07
---

# Zero-prompt golden path

- makes `wisk start` the canonical ordinary-work entrypoint with an optional task;
- resumes compatible live LoopRuns from persisted state instead of creating duplicate scaffolds;
- returns stable `next`, `blocked`, and `done` operation envelopes and propagates next state after typed run mutations;
- makes SessionType and RunSpec structural overrides explicit while retaining deprecated compatibility forms;
- persists repository provenance on Handoffs and requires environment revalidation plus explicit handoff disposition before continuation;
- exposes the same start semantics through FastMCP and the Cyclopts terminal adapter;
- rejects silent fallback to a generic `knowledge/` directory in uninitialized consumer repositories;
- updates bootstrap, documentation, and installed-wheel smoke coverage to the `wisk init` once / `wisk start` recurring lifecycle.
