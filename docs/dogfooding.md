# Progressive Dogfooding Protocol

`wisk` develops itself through the same execution and learning runtime it offers to consumers.

## Contract-guided development

Before substantive work, an agent development session should create a live `LoopRun` governed by `knowledge/run-specs/wisk-development.md`.

The run starts intentionally incomplete and is filled as the session advances with:

- `RunReading` for repository guidance, issues, PRs, OKF knowledge and recent runs;
- `RunGoal` with an observable `success_signal`;
- `RunDecision` for consequential choices;
- `RunEvidence` for changes and observed results;
- `RunCheck` for OKF/tests/other verification;
- `RunOutcome` describing the state reached and next natural move.

The agent repeatedly validates the bundle with `okf-parser` and uses unsatisfied run requirements as operational feedback.

## Learning after execution

The run graph is the evidence-rich source for the persistent learning cycle:

```text
LoopRun / RunEvidence
  -> Experience
  -> WikiEntry
  -> AgentSkill / SkillProposal
  -> SkillEvaluation
  -> evolved skill and/or RunSpec
```

## Dogfooding phases

### Phase 0 — Manual contract bootstrap

Core execution and learning specs are written by hand in OKF while the runtime surface is being implemented.

### Phase 1 — Contract-guided manual runs

Development sessions use the dogfood `RunSpec` and maintain `LoopRun` plus typed run components directly in the bundle. `okf-parser` supplies validation feedback.

### Phase 2 — Runtime-assisted start/check

Once `wisk start` / `wisk check` and equivalent FastMCP tools exist, run scaffolding and requirement inspection move behind the runtime API.

### Phase 3 — Experience consolidation

Completed and partial run evidence is distilled into `Experience` and then into durable `WikiEntry` knowledge.

### Phase 4 — Skill and RunSpec evolution

Changes to procedural skills and execution contracts are proposed/evaluated through `SkillProposal` and `SkillEvaluation`, retaining asymmetric rollback: rejected procedures can roll back while evidence and knowledge remain.

### Phase 5 — MCP-driven operation

Agent sessions primarily operate through `wisk_*` FastMCP tools, with the OKF graph remaining the durable source of truth.
