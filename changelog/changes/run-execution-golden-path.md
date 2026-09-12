---
type: Changelog
version: 0.4.0rc1
date: 2026-09-08
---

# Real command execution in Work traces

- adds `RunExecution` as the objective subprocess record in the Work Raw Layer;
- makes CLI `wisk run -- <argv>` execute direct argv and capture timing, exit status, output digests, cwd, Git state, and `next` before/after;
- supports explicit command-bound projections through `--evidence`, `--check`, `--observe`, and `--using skill@version` while keeping semantic meaning separate from process success;
- keeps `--why` and `--expect` as concise pre-execution declarations rather than chain-of-thought or implicit RunGoal/RunDecision records;
- moves manual typed CLI writes to `wisk record ...` and promotes `wisk trace` to the top level;
- exposes real execution through MCP only in the server environment it actually controls;
- reports `effect_may_have_occurred` when persistence fails after a command may already have changed external state.
- patches `next_after` through the parser's transactional scalar writer without updating generated schema columns or degrading the stored execution facts; regression tests cover zero exit codes, booleans, repeated updates, write failures, and raw output digests.
