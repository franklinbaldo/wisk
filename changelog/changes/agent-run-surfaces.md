---
type: Changelog
version: 0.2.11
date: 2026-09-06
---

# Agent-facing session and run surfaces

- adds MCP tools for starting the next eligible session and recording every typed live-run component;
- adds CLI `session next` / `session start-next` and `run reading|goal|decision|evidence|check|outcome` commands;
- allows the core MCP and CLI context/start/check operations to target an explicit Wisk bundle path;
- exposes `target_session_type` through CLI handoff creation;
- keeps each mutation effect-explicit and delegates persistence to the validated Wisk runtime service layer.
