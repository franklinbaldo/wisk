---
title: "RFC 0006 — Zero-prompt golden path"
status: proposed
created: 2026-09-07
supersedes:
  - "RFC 0005: consumer golden path entrypoint"
---

# RFC 0006 — Zero-prompt golden path

## Summary

After a repository adopts Wisk, ordinary agent execution should require no orchestration prompt and no knowledge of Wisk's internal scheduling vocabulary.

The consumer golden path becomes:

```bash
# once
wisk init

# every ordinary work session
wisk start
```

`wisk start` means: resume useful work when a compatible live run already exists; otherwise select the best eligible SessionType and start the best useful work available in the repository.

Optional constraints are explicit exceptions:

```bash
wisk start --session-type wiki
wisk start --run-spec local-review
wisk start "Improve CLI ergonomics"
wisk start "Review current knowledge" --session-type wiki
```

RFC 0006 supersedes the operational golden-path entrypoint and explicit-start semantics of RFC 0005. RFC 0005 remains authoritative for the broader consumer/product boundary, managed state, bootstrap/upgrade ownership, standard profile, and local specialization except where this RFC changes invocation semantics.

## Motivation

The previous consumer quickstart exposed implementation details:

```bash
wisk init .
wisk session start-next "Do the best useful work available in this repository"
```

The normal caller should not need to repeat the repository default, know the scheduler's `start-next` vocabulary, or restate Wisk's generic purpose.

The current public surface also duplicates operations between Cyclopts and FastMCP, and `wisk start` currently exposes positional task, RunSpec, and SessionType arguments. This RFC therefore reshapes an existing interface rather than merely adding a shorter alias.

A further requirement follows from unattended scheduling: a scheduler may invoke `wisk start` after a process crash or while a previous run remains in `scaffold` or `active`. The runtime must recover from persisted state instead of accumulating orphan scaffolds or requiring process memory.

## Design principles

**Defaults encode policy; arguments encode exceptions.**

**Define operations once.** A Wisk operation has one canonical typed definition. CLI and MCP are transport/presentation surfaces, not independent behavioral APIs.

**Persisted state drives execution.** Every state-changing Wisk operation MUST return the next actionable contract state or a terminal state, and that next state MUST be derivable solely from persisted OKF state plus the operation's explicit inputs. Process-local memory must not be required to resume a run.

A useful acceptance test is:

> After `wisk init`, can an unattended scheduler invoke only `wisk start` indefinitely, across process restarts, without maintaining a second orchestration prompt or run-local memory?

The answer should be yes.

## Canonical operation surface

FastMCP tools are the canonical typed public operation definitions for operations that naturally map to MCP tools.

Conceptually:

```python
@mcp.tool(name="start")
def start(
    task: str | None = None,
    *,
    session_type: str | None = None,
    run_spec: str | None = None,
) -> OperationResult:
    ...
```

The runtime/domain layer owns behavior. The canonical tool owns the public typed schema. The CLI is generated/projected from that schema when practical, or implemented as a thin Cyclopts adapter when terminal-specific UX materially improves usability. A handwritten CLI adapter must delegate to the same canonical operation and must not redefine defaults, selection, errors, or result semantics.

This rule applies progressively to other duplicated Wisk operations, not only `start`.

## Proposed interface

### Bootstrap

```bash
wisk init
```

`init` defaults to the current working directory. An explicit repository remains supported:

```bash
wisk init ../consumer
```

`init` is bootstrap, not a per-session operation.

### Ordinary execution

```bash
wisk start
```

With no arguments, Wisk:

1. resolves the initialized consumer repository;
2. evaluates SessionType eligibility, cadence, priority, and blockers;
3. determines the SessionType that ordinary selection would target;
4. checks persisted state for a compatible live LoopRun in `scaffold` or `active`;
5. if a compatible live run exists, resumes it by recomputing and returning its current actionable state;
6. otherwise, if policy permits a new run, selects the best eligible SessionType;
7. uses Wisk's internal default intent to do the best useful work available in the repository;
8. resolves RunSpec, context policy, and compatible handoff state;
9. creates the live run scaffold;
10. returns the canonical operation envelope including the next actionable state.

The literal default task string is an internal product detail. It must not become consumer configuration or determine every run's human-facing title.

### Explicit task

```bash
wisk start "Improve CLI ergonomics"
```

The task is optional. Supplying it constrains the work while ordinary SessionType selection remains in effect unless the caller also supplies a structural override.

### Named structural overrides

RunSpec and SessionType are structural controls and must be named:

```bash
wisk start --session-type wiki
wisk start --run-spec local-review
wisk start "Review current knowledge" --session-type wiki --run-spec local-review
```

The equivalent MCP operation exposes the same fields with the same defaults.

## Start is resumable and idempotent over compatible live work

`wisk start` is not blindly "create a run". It is the idempotent golden-path operation for entering useful work.

If persisted OKF state already contains a compatible LoopRun in `scaffold` or `active`, `start` should return that run and its recomputed `next` state rather than create a duplicate.

Compatibility must be determined from persisted, auditable data: selected/pinned SessionType, effective RunSpec, explicit task constraints where relevant, and policy. It must not depend on process-local session state.

`max_parallel` remains authoritative. The existence of one active run does not universally forbid another; rather:

- when policy does not permit another compatible parallel run, `start` resumes the existing run;
- when policy permits parallelism and the caller's explicit constraints distinguish a new run, creation may proceed;
- ordinary zero-prompt scheduling should prefer resumption over multiplying indistinguishable scaffolds.

If persisted state is ambiguous in a way policy cannot resolve safely, the operation returns `blocked` with structured remediation rather than guessing.

This makes crash recovery, scheduler restarts, and repeated hourly invocation all use the same operation.

## SessionType override semantics

`--session-type X` is an explicit override.

It bypasses positive eligibility reasons such as interval, threshold, or `on_demand`, and records `selection_reason: explicit-override`.

It does **not** bypass blockers such as cooldown, max parallelism, hourly budget, or other hard safety/resource blockers.

`on_demand` remains a scheduling/fallback signal and must not be overloaded to mean explicit user override. A SessionType may have `on_demand: false` and still be explicitly startable by id.

## Canonical operation envelope

Expected domain states are returned through one stable envelope rather than split between successful payloads and generic exceptions.

Conceptually:

```json
{"run": "runs/123", "state": "next", "next": {"operation": "run_reading", "required": ["kind", "reference", "finding"]}}
```

```json
{"run": null, "state": "blocked", "blockers": ["hourly-budget"], "remediation": [{"action": "retry_later"}]}
```

```json
{"run": "runs/123", "state": "done"}
```

The stable state vocabulary begins with:

- `next`: the run has an actionable contract requirement;
- `blocked`: expected policy/domain state currently prevents progress;
- `done`: the operation/run has reached a terminal successful state.

Additional terminal failure/cancelled states may be introduced when the lifecycle contract requires them, but callers should not need separate parsers for normal progress and expected blocking.

Expected cadence, eligibility, budget, or parallelism blocking is domain state and should not be represented as a generic `ValueError`. Exceptions remain appropriate for exceptional conditions such as corrupted bundles, invalid persisted invariants, or I/O/runtime failures.

## `next` is a stable contract

The existing runtime already computes unsatisfied requirements through `check_run`; RFC 0006 promotes that capability into the public operation contract.

Every state-changing operation MUST return either:

- `state: next` plus a structured `next` action;
- `state: blocked` plus structured blockers/remediation; or
- a terminal state such as `done`.

`next` is not primarily a shell command. It is a transport-neutral description of the next typed operation and the information required to satisfy it. A CLI adapter may additionally render a convenient literal command for humans, but command text is presentation rather than the canonical protocol.

The decisive invariant is:

> `next` MUST be a pure function of persisted OKF state and explicit operation inputs.

A fresh process opening the same initialized repository must be able to recompute the same actionable contract state without receiving hidden state from the process that created the run.

This property lets the runtime drive the agent instead of merely recording what an external prompt decided to do.

## Handoffs

A compatible pending handoff is execution state, not a reason for the caller to choose another command.

When no compatible live run already exists and policy selects handoff continuation, `wisk start` creates a **fresh LoopRun of the target SessionType with the handoff injected into context**. It does not reopen the historical run that produced the handoff.

The new LoopRun records the handoff reference, for example as `resumed_handoff`, and the selection reason.

The handoff is **not archived at start**. It remains active until an outcome successfully consumes or supersedes it. A failed/interrupted resumed run therefore does not erase the recovery path.

If the resumed LoopRun itself remains live across a process restart, subsequent `wisk start` invocations resume that live LoopRun through the same idempotent-start rule; they do not create another handoff-consumer run.

When several compatible handoffs exist and the caller supplies a task, existing relevance ordering may be used. With no explicit task, initial selection is deterministic: oldest compatible active handoff first. A later RFC may introduce explicit Handoff priority without changing `wisk start`.

## Run identity under zero-prompt

The internal default intent must not cause every zero-prompt run to have the same title/slug.

When no task is supplied, the human-facing title should derive from selected SessionType and resolved work/context. The effective default intent remains separately auditable.

## Initialized-repository boundary

`wisk start` requires an initialized consumer repository.

Path resolution must not silently reinterpret an uninitialized repository as Wisk's dogfood `knowledge/` layout. Failure should be concise and actionable, directing the caller to `wisk init`.

Dogfood/development layout support may remain only when positively identified. Repository/path overrides may exist at lower layers or through explicit advanced configuration; they are not part of the ordinary golden path.

## Runtime responsibilities

Zero-prompt moves orchestration knowledge to the component that owns it.

The runtime should own:

- resumable live-run discovery;
- SessionType eligibility, cadence, priority, blockers, and explicit pinning;
- compatible handoff continuation;
- RunSpec and context-policy resolution;
- scaffold creation;
- derivation of the next unsatisfied contract requirement from persisted state;
- validation after state transitions;
- structured blockers and remediation;
- actionable guidance through the canonical envelope.

Low-level operations such as run reading, goal, decision, evidence, check, and outcome remain useful primitives. They should participate in the same state envelope and return the newly derived `next`/terminal state after mutation.

## Inspection remains separate

Inspection operations such as `session next` may remain available for debugging and scheduler introspection, but the golden path does not require a caller to inspect and then manually translate the answer into another start operation.

A later RFC may aggregate these views into a human-oriented status surface.

## FastMCP and CLI projection

For tool-shaped operations, FastMCP defines the canonical typed public schema.

The CLI projection must preserve operation name, parameter names/types, optionality/defaults, structural named arguments, result semantics, and expected error states.

Machine-readable operation output is canonical. Human-readable CLI presentation, including optional command hints or JSON/text formatting, may evolve independently as long as semantics remain identical.

The target architecture is:

```text
Wisk runtime/domain behavior
          ↑
canonical typed FastMCP operations
          ↑
MCP transport + CLI projection/thin terminal adapters
```

not independently specified CLI and MCP APIs.

## Lifecycle

```bash
wisk init       # first adoption
wisk start      # start or resume ordinary useful work
wisk upgrade    # explicit managed-bundle refresh
```

`start` must not implicitly run `init` or `upgrade`.

A distinct `continue` command is not required for the golden path: resumability belongs to `start` plus persisted state. A future convenience command may expose active-run inspection without becoming a second orchestration primitive.

Session finalization (`finish`) is intentionally outside this RFC because transactional outcome/Experience/Handoff policy deserves a separate lifecycle design.

## Compatibility and migration

Implementation should:

- make task optional in canonical start;
- default repository arguments appropriately for initialized consumers;
- move positional RunSpec selection to `--run-spec` / named MCP field;
- move positional SessionType selection to `--session-type` / named MCP field;
- preserve unambiguous legacy positional forms for a deprecation window with warnings;
- retain `session start-next` and `wisk_start_next_session` as compatibility aliases during deprecation;
- converge duplicated Cyclopts/FastMCP definitions toward canonical FastMCP tools plus projection/thin adapters;
- promote `check_run`'s next typed action into the stable operation envelope;
- treat expected blockers as typed domain returns rather than generic exceptions;
- make `start` resume compatible persisted live runs before creating duplicates;
- keep RFC 0005's supersession annotations current.

## Consumer integration

A consumer installing Wisk in its project environment should reduce a recurring loop to:

```bash
uv run wisk start
```

The scheduler can safely issue that command again after a process restart or on its next cadence tick. Persisted OKF state determines whether Wisk resumes existing work, reports a blocker, or creates a new run.

The consumer should not reproduce Wisk's orchestration algorithm in prompts. Domain-specific requirements remain consumer-owned SessionTypes, RunSpecs, context policies, and knowledge.

## Non-goals

This RFC does not:

- remove SessionTypes, RunSpecs, context policies, cadence, or low-level run-state operations;
- allow explicit override to bypass hard blockers;
- make `init` or `upgrade` implicit;
- require `start` to perform arbitrary autonomous shell/GitHub actions;
- archive handoffs at start;
- reopen historical LoopRuns when consuming a handoff;
- define transactional session finalization (`finish`);
- define a consolidated human `status` UI;
- require a separate `continue` command;
- require every terminal interaction to be generated from FastMCP when a thin parity-tested terminal adapter is demonstrably better.

## Acceptance criteria

The RFC is implemented when:

1. `wisk init` initializes the current repository without requiring `.`.
2. `wisk start` works with no task.
3. no-task execution uses Wisk's standard useful-work intent without deriving every run title from its literal text.
4. `wisk start "task"` supports an explicit task.
5. `--session-type` bypasses eligibility reasons, records `explicit-override`, and honors hard blockers.
6. `--run-spec` pins RunSpec explicitly.
7. ordinary fresh-run selection remains driven by eligibility, cadence, priority, and handoff policy.
8. `start` detects and resumes a compatible persisted `scaffold`/`active` LoopRun instead of creating an indistinguishable duplicate when policy does not permit/justify another.
9. `max_parallel` participates in the resume-vs-create decision.
10. process restart does not change the derived next actionable state for unchanged persisted OKF state and explicit inputs.
11. compatible handoff continuation creates a fresh consumer run, records the handoff, and leaves it active until successful outcome.
12. repeated `start` after handoff-run creation resumes that live consumer run rather than creating another.
13. multiple zero-prompt handoffs are selected deterministically.
14. uninitialized consumer repositories fail clearly rather than falling through to dogfood layout.
15. every state-changing operation returns one canonical envelope with `state` and either `next`, blockers/remediation, or terminal state.
16. expected cadence/eligibility/resource blocking is represented as `state: blocked`, not generic exceptions.
17. `next` is derivable solely from persisted OKF state plus explicit operation inputs.
18. FastMCP exposes the canonical typed start operation and the CLI projects/adapts it without semantic drift.
19. `session start-next` / `wisk_start_next_session` are no longer presented as the golden path.
20. RFC 0005 points to RFC 0006 for canonical entrypoint and explicit-start semantics.
21. tests cover zero-prompt start, explicit task, overrides, reasons/blockers, RunSpec pinning, live-run resume, process-restart recovery, max_parallel, handoff continuation, uninitialized repositories, envelope stability, MCP/CLI parity, and compatibility behavior.

## Consequence

The architectural change is not merely a shorter command. It is ownership of execution state.

A consumer describes what is special about its work. Wisk owns how Wisk operates, persists enough state to reconstruct what happens next, and exposes each public operation once.

After adoption, the recurring instruction collapses to:

```bash
wisk start
```

Whether that call begins new work or resumes interrupted work is determined by persisted, auditable Wisk state. That is the zero-prompt golden path.
