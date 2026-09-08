# Wisk

> **Contract-guided agent execution and persistent learning on OKF.**

`wisk` is an experimental agent runtime inspired by the Google Research paper **[“WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution”](https://arxiv.org/abs/2608.27454)** by Liyan Tang, Cyrus Rashtchian, Chun-Sung Ferng, Andrew Tomkins, Da-Cheng Juan, and Tu Vu (2026).

WikiSkill's separation between **raw execution experience**, **persistent wiki knowledge**, and **executable skills** is a primary architectural influence on Wisk. Wisk adds a repository-oriented, contract-guided runtime around that learning cycle. When a Wisk design or consumer specialization is ambiguous, the paper is an explicit reference for the intended Experience → Wiki → Skill semantics; Wisk's own RFCs define the product-specific extensions and operational contracts.

It uses [Open Knowledge Format (OKF)](https://github.com/franklinbaldo/okf-parser) to represent live execution state and persistent learning as an auditable typed knowledge graph.

## Consumer quickstart

Wisk is intended to be adopted by an existing repository, not reconstructed from a long prompt.

For a project managed with `uv`, install Wisk from PyPI as a normal project dependency and run it through that project's environment:

```bash
uv add wisk
uv sync
uv run wisk init
uv run wisk start
```

`wisk init` creates a managed `.wisk/` bundle containing compatible normative contracts, canonical learning roles, the standard consumer profile, and Wisk's managed consumer-adoption guidance. It is a one-time adoption step; ordinary scheduled or interactive work thereafter enters through `wisk start` (for example, `uv run wisk start` in a `uv` project).

`wisk start` needs no task. It resumes compatible live work when present; otherwise it selects the best eligible SessionType and returns the next typed contract action. Optional task, SessionType, and RunSpec constraints remain available:

```bash
uv run wisk start "Improve CLI ergonomics"
uv run wisk start --session-type wiki
uv run wisk start --run-spec local-review
```

Managed runtime files can be refreshed explicitly with:

```bash
uv run wisk upgrade
```

Upgrade checks hashes before writing. If a Wisk-managed file was edited locally, the command reports a conflict and leaves the installation untouched. Consumer-owned files and runtime knowledge are never overwritten by managed upgrade.

See [RFC 0006](docs/rfc/0006-zero-prompt-golden-path.md) and [RFC 0005](docs/rfc/0005-consumer-golden-path.md).

## What Wisk does

Agent repositories face two related problems:

1. a session can start from a prompt with weak structural guidance about what good execution must establish;
2. useful lessons from execution are easily lost or mixed into unstructured memory.

Wisk addresses both.

A work session starts from a typed `RunSpec`, creates an intentionally incomplete `LoopRun`, and progressively records readings, goals, decisions, evidence, checks, and an outcome. `okf-parser` validation makes missing contract state visible while the work is still happening.

```text
RunSpec
  → LoopRun scaffold
  → RunReading / RunGoal / RunDecision / RunEvidence / RunCheck
  → RunOutcome
  → Experience
```

That raw episodic evidence feeds the canonical three-role learning cycle:

```text
Skill creates/refines a candidate
              ↓
Experience executes real work and records what happened
              ↓
Wiki synthesizes and compares durable evidence
              ↓
Skill revisits the candidate and decides its lifecycle
              └──────────────→ next Experience
```

The canonical roles are **Experience**, **Wiki**, and **Skill**. Experience owns observation, not synthesis: it records truthful episodic evidence and does not decide that a lesson should become a `WikiEntry` or change an `AgentSkill`. Wiki owns synthesis across Experiences; Skill owns procedural intervention and lifecycle decisions. `SkillEvaluation` remains available as an optional explicit benchmark/review artifact when useful.

See [RFC 0004](docs/rfc/0004-canonical-learning-cycle.md) and the [WikiSkill paper](https://arxiv.org/abs/2608.27454).

## Standard profile

`wisk init` installs an opinionated but replaceable standard profile.

- **Experience** is ordinary useful work and is the on-demand fallback for `wisk start` when no higher-priority synthesis or skill evolution is due.
- **Wiki** becomes eligible after three new Experiences and has higher priority than ordinary Experience.
- **Skill** becomes eligible after six new Experiences. Wiki has higher priority, so synthesis runs before skill evolution when both are due.

The default rhythm is roughly:

```text
Experience × 3 → Wiki
Experience × 3 → Wiki → Skill
repeat
```

Those thresholds are product defaults, not universal laws. Consumers can specialize SessionTypes, RunSpecs, context policies, and cadence without redefining the core learning roles.

## Contract-guided execution

The run artifact is not a report written after the work. It exists before substantive execution begins.

```text
wisk start
→ validate persisted state
→ inspect the next unsatisfied requirement
→ perform the next useful action
→ record typed state and evidence
→ validate again
→ leave a coherent outcome or handoff
```

Core concepts include `RunSpec`, `LoopRun`, `RunReading`, `RunGoal`, `RunDecision`, `RunEvidence`, `RunCheck`, `RunOutcome`, and `Handoff`.

Consumers specialize `RunSpec` rather than forcing domain rules into Wisk core. Software development, journalism, legal work, research, and other domains can require different readings, evidence, checks, and result states while sharing the same runtime.

## Persistent learning

- **`Experience`** — truthful raw episodic evidence from real execution.
- **`WikiEntry`** — durable knowledge synthesized across experiences.
- **`AgentSkill`** — reusable procedural guidance; active and experimental versions may coexist.
- **`SkillProposal`** — explicit change record/rationale for procedural evolution.
- **`SkillEvaluation`** — optional explicit benchmark or review record.

Procedural state is reversible while evidence and durable knowledge are cumulative. A weak candidate skill can be rejected without losing the experience that showed why it failed.

## CLI

Important entry points include:

```text
wisk init [repository]
wisk start [task] [--session-type ...] [--run-spec ...]
wisk upgrade [repository]
wisk check <run>
wisk context <task>
wisk session next
wisk session start-next <task>   # compatibility alias
wisk run reading|goal|decision|evidence|check|outcome ...
wisk experience preview|record ...
wisk handoff list|create|continue ...
wisk serve
```

## Python API

```python
from wisk import Wisk
```

## Architecture boundary

```text
okf-parser
  ├── Markdown/frontmatter parsing
  ├── concept identity and graph traversal
  ├── Ibis / DuckDB / NetworkX integration
  └── schema compilation and validation

wisk
  ├── RunSpec + live execution semantics
  ├── SessionType + policy/cadence composition
  ├── experience and knowledge consolidation
  ├── skill evolution lifecycle
  ├── consumer bootstrap + upgrade
  └── CLI + FastMCP runtime
```

Wisk does not duplicate generic parsing or validation machinery from `okf-parser`.

## Development and dogfooding

Wisk develops itself through the same runtime. The repository's own `knowledge/` tree is a dogfood consumer with additional development-specific SessionTypes and policies.

The canonical Experience/Wiki/Skill roles are deliberately policy-neutral so other repositories do not inherit Wisk's software-development assumptions.

See [docs/architecture.md](docs/architecture.md) and [docs/dogfooding.md](docs/dogfooding.md).

## Development setup

```bash
git clone https://github.com/franklinbaldo/wisk.git
cd wisk
uv sync
uv run wisk info
```

## License

MIT © Franklin Baldo
