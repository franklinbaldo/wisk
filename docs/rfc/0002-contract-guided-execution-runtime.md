# RFC 0002 — Contract-guided execution runtime

Status: Proposed

Issues: #27, #28, #29, #30

## Summary

Wisk evolves from a persistent learning runtime into a **contract-guided agent execution runtime with persistent learning**.

The core execution flow becomes:

```text
RunSpec
  -> LoopRun scaffold
  -> repeated validation + work + evidence
  -> RunOutcome
  -> Experience
  -> WikiEntry
  -> SkillProposal
  -> SkillEvaluation
  -> evolved skill / RunSpec
```

A run starts intentionally incomplete. Its `RunSpec` defines the state, readings, goals, evidence and checks that make a useful run well formed. `okf-parser` validates the live OKF graph repeatedly while the agent works. Missing or unsatisfied parts of the graph are operational feedback for the next step.

This makes the run artifact simultaneously a plan, checklist, state machine, evidence ledger, memory boundary and handoff.

## Motivation

Wisk already models what an agent learned after execution through `Experience`, `WikiEntry`, `AgentSkill`, `SkillProposal`, `SkillEvaluation`, and `LoopRun`. The missing layer is the contract that guides the execution itself.

A retrospective trace cannot tell an agent, at the beginning of a session, what evidence is still needed or which preconditions remain unsatisfied. Consumers currently need to reinvent this logic in prompts.

The new architecture moves that logic into typed OKF contracts.

## Principles

### The run is live state, not a post-hoc report

`LoopRun` exists before meaningful work begins. It is scaffolded from a `RunSpec`, starts incomplete, and is updated throughout the session.

### Validation is operational feedback

`okf-parser` is used throughout the run. Validation is not merely a final CI gate. The agent repeatedly asks what the current run graph still lacks and uses that answer to select the next useful action.

### Evidence is first-class

Claims about progress should be linked to `RunEvidence` and `RunCheck` records rather than represented only as prose or booleans.

### Goals are observable

A `RunGoal` carries a `success_signal` describing what observable state would count as advancement.

### Domain contracts specialize the generic runtime

Wisk provides generic execution concepts. A software-development skill, newsroom skill, legal-analysis skill, research skill, or consumer repository can define a specific `RunSpec` that requires domain-specific readings, evidence and completion conditions.

### Contracts are evolvable

Types, specs and schemas are living architecture. A run may produce evidence that the current `RunSpec` or skill contract is inadequate; that evidence can feed the normal `Experience -> WikiEntry -> SkillProposal -> SkillEvaluation` learning cycle and improve future runs.

## Core concepts

### RunSpec

Defines the protocol for a class of runs. It may describe required reading categories, required goal/evidence/check categories, allowed states, completion expectations and the skill it belongs to.

### LoopRun

Concrete live instance of a `RunSpec`. It points to the run components accumulated during execution and records the current state.

### RunReading

Records a source or artifact consulted during the run and the relevant finding derived from it.

### RunGoal

An intended advancement with rationale and observable `success_signal`.

### RunDecision

A consequential choice made during execution, including rationale and optional linkage to the goal it advances.

### RunEvidence

A typed piece of evidence such as test output, CI result, runtime observation, diff, source, issue, PR, review, benchmark or OKF validation result.

### RunCheck

A verification performed during the run, with procedure/command, result and optional evidence linkage.

### RunOutcome

Represents the state reached by the end of the current run and the next natural continuation. A run can end coherently without completing an entire feature.

## Relationship to existing learning concepts

The execution layer does not replace the learning layer.

`Experience` remains episodic evidence distilled from what happened. `WikiEntry` remains durable knowledge. `AgentSkill` remains reusable procedural guidance. `SkillProposal` and `SkillEvaluation` remain the controlled evolution mechanism.

The change is that these concepts now consume a much richer, typed execution graph rather than a mostly retrospective trace.

## Skill relationship

An `AgentSkill` may reference a default `RunSpec`. Consumers can provide more specific specs.

Examples:

- `software-development` may require repository context, issue/PR state, behavior goals, RED/GREEN evidence and checks;
- `news-investigation` may require lead, sources, hypotheses, provenance, contradiction and editorial checks;
- `legal-analysis` may require records read, issues framed, authorities, risk evidence and conclusion;
- `research` may require question, literature/evidence, experiment or analysis, result and limitations.

The generic runtime should not encode these domain rules directly.

## Runtime surface

The desired runtime API is conceptually:

```text
wisk_start(task, run_spec?)
  -> selects/loads a RunSpec
  -> creates an intentionally incomplete LoopRun scaffold
  -> returns initial context and requirements

wisk_check(run)
  -> validates the live OKF graph
  -> returns unsatisfied requirements and current state
```

CLI and FastMCP should expose equivalent operations. These operations must reuse `okf-parser` rather than implement a competing validation engine.

## Dogfooding

Wisk should use this protocol to develop itself. The repository will define a development `RunSpec` and store its own live/completed runs in `knowledge/`.

This makes the project exercise the same protocol offered to consumers and gives the learning layer real execution evidence to evolve against.

## Migration

`LoopRun` changes semantics from primarily retrospective traceability to a live execution record. Existing runs remain useful historical records; new runs should reference a `RunSpec` and accumulate typed run components.

The migration should proceed incrementally:

1. define core specs and semantics;
2. add a dogfood `RunSpec`;
3. add runtime `start`/`check` surfaces;
4. make completed run evidence feed Experience consolidation;
5. allow AgentSkill/SkillProposal evolution to update RunSpecs as well as procedural text.

## Success criteria

The pivot succeeds when an agent can enter a repository with a task, start a Wisk run, receive an intentionally incomplete typed scaffold, work while repeatedly validating it, and leave behind a graph that both explains the achieved state and makes the next continuation obvious.
