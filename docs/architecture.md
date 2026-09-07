# Architecture & Design Boundaries

`wisk` is a persistent agent runtime built on OKF. Its central job is now twofold:

1. guide live agent execution through typed, progressively satisfied run contracts;
2. compile evidence from those runs into persistent knowledge and evolving skills.

## 1. Separation of responsibilities

```text
┌────────────────────────────────────────────────────────┐
│                   okf-parser                           │
│  - Generic OKF parser, AST, link resolution            │
│  - NetworkX graph generation & Ibis/DuckDB backend     │
│  - Universal schema generation & format validation     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                   wisk                            │
│  - RunSpec + contract-guided live execution            │
│  - LoopRun state, goals, readings, evidence, checks    │
│  - Experience, Wiki, Skills, evaluation & evolution    │
│  - Context extraction, lineage & impact inspection     │
│  - High-level CLI (Cyclopts) & MCP server (FastMCP)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                  Consumers                             │
│  - wisk itself (primary dogfooding consumer)      │
│  - software-development agents                         │
│  - newsroom / research / legal / other workflows       │
└────────────────────────────────────────────────────────┘
```

### Invariants

1. `wisk` does not reimplement frontmatter parsing, link resolution, graph compilation, schema compilation, or DuckDB translation.
2. `okf-parser` remains domain-neutral and does not contain Wisk-specific execution or learning semantics.
3. Run completion semantics belong to `RunSpec` contracts, not hard-coded branches in the runtime.
4. Runtime operations such as `start` and `check` should use `okf-parser` as the source of structural truth.

## 2. Execution layer

The execution layer exists before the learning layer:

```text
RunSpec
   │
   ▼
LoopRun scaffold
   │
   ├── RunReading
   ├── RunGoal
   ├── RunDecision
   ├── RunEvidence
   ├── RunCheck
   └── RunOutcome
```

A `LoopRun` starts intentionally incomplete. The agent repeatedly validates the live OKF graph, inspects unsatisfied requirements, performs useful work, records evidence, and validates again.

The run artifact therefore acts as:

- operational plan;
- typed checklist;
- state machine;
- evidence ledger;
- session memory;
- handoff to the next run.

A `RunSpec` is domain-neutral infrastructure with domain-specific instances. Wisk core defines generic component types; consumer skills and repositories define which categories of reading, goals, evidence and checks matter.

## 3. Learning layer

Wisk has three canonical learning roles, expressed as `SessionType`s:

```text
        ┌─────────────────────────────────────────┐
        │                 Skill                   │
        │ create/refine candidate or decide state│
        └───────────────────┬─────────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────────┐
        │              Experience                 │
        │ execute real work with incumbent and/or│
        │ candidate; record what actually happens│
        └───────────────────┬─────────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────────┐
        │                  Wiki                   │
        │ synthesize and compare durable evidence│
        └───────────────────┬─────────────────────┘
                            │
                            └──────────────► Skill
```

The canonical roles are:

- **Experience**: executes real work and records episodic evidence, including which skill/version actually guided the execution;
- **Wiki**: consolidates multiple experiences into durable knowledge and, when relevant, compares incumbent and candidate behavior;
- **Skill**: changes future procedural behavior by creating, refining, promoting, rejecting, deprecating, or replacing skill guidance.

Skill evaluation is therefore cross-session lineage, not a mandatory fourth orchestration role. A `SkillEvaluation` may still exist as an optional explicit benchmark or decision artifact, and consumers may define evaluator sessions when useful, but the learning cycle does not depend on them.

A typical candidate lifecycle is:

```text
SkillProposal + experimental AgentSkill
        │
        ▼
Experience(skill_used, skill_version)
        │
        ▼
WikiEntry(evidence=[...])
        │
        ▼
Skill session decision
        └────► refine / continue experiment / promote / reject
```

This retains the asymmetric rollback principle: procedural state may be rolled back while evidence and durable knowledge remain.

The consequence is that Wisk can learn not only *what an agent should know* and *how it should act*, but also *how future executions should be structured and validated*.

## 4. Concept graph

All concepts are standard OKF Markdown documents under `knowledge/`.

Learning concepts:

- `knowledge/experiences/`: episodic evidence distilled from runs;
- `knowledge/wiki/`: consolidated durable knowledge;
- `knowledge/skills/`: active and experimental agent procedural skills;
- `knowledge/proposals/`: candidate skill/spec evolution records;
- `knowledge/evaluations/`: optional benchmark and decision evidence when explicitly materialized.

Execution concepts:

- `knowledge/run-specs/`: operational contracts;
- `knowledge/runs/`: live and completed `LoopRun` instances;
- run components may live beside a run or in typed subdirectories as the bundle conventions evolve.

Lineage is expressed through OKF links so the graph can answer questions such as:

- which evidence supported this run outcome?
- which run produced this Experience?
- which skill/version guided that Experience?
- which experiences justified this WikiEntry?
- which proposal introduced the experimental candidate?
- what Wiki synthesis justified promoting, revising, or rejecting it?

## 5. Runtime surface

Current runtime surfaces (`inventory`, `context`) remain useful. The target execution API adds:

```text
start(task, run_spec=None)
check(run)
```

`start` selects or receives a `RunSpec`, creates a scaffold before substantive work, and returns the initial execution context.

`check` validates the live run and exposes unsatisfied requirements/current state so the agent can decide what to do next.

CLI and FastMCP should expose equivalent semantics.

## 6. Consumer specialization

The generic execution vocabulary deliberately does not encode software-development, newsroom, legal, or research rules.

Consumers should normally specialize one of the three canonical learning roles:

- an ordinary software-development, newsroom, legal, or research work session is usually an **Experience** specialization;
- durable synthesis or curation is a **Wiki** specialization;
- changes to reusable procedural guidance are a **Skill** specialization.

Examples of specialized Experience contracts:

- software development: repo/issue/PR readings, behavior goals, RED/GREEN evidence, CI and review checks;
- newsroom: lead, source readings, provenance, contradiction, editorial evidence and publication state;
- legal analysis: records read, issues framed, authorities, risk evidence and conclusion;
- research: question, literature/evidence, experiment/analysis, result and limitations.

Consumer RunSpecs may add domain-specific checks. The core roles define responsibility and lineage; they do not hard-code domain quality criteria.

This keeps Wisk reusable while making consumer sessions more structured and auditable than prompt-only workflows.
