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

The consumer golden path is:

```bash
# once
wisk init

# ordinary work, including crash/restart recovery
wisk start
```

`wisk start` resumes compatible live work when it exists; otherwise it selects the best eligible SessionType and starts the best useful work available in the repository.

Optional constraints encode exceptions:

```bash
wisk start --session-type wiki
wisk start --run-spec local-review
wisk start "Improve CLI ergonomics"
wisk start "Review current knowledge" --session-type wiki
```

RFC 0006 supersedes RFC 0005's operational golden-path entrypoint and explicit-start semantics. RFC 0005 remains authoritative for the broader consumer/product boundary, managed state, bootstrap/upgrade ownership, standard profile, and local specialization except where this RFC changes invocation semantics.

## Motivation

The previous consumer quickstart exposed implementation details:

```bash
wisk init .
wisk session start-next "Do the best useful work available in this repository"
```

The normal caller should not need to repeat the repository default, know the scheduler's `start-next` vocabulary, or restate Wisk's generic purpose.

The current public surface also duplicates operations between Cyclopts and FastMCP, while `wisk start` currently exposes positional task, RunSpec, and SessionType arguments. This RFC therefore reshapes an existing interface rather than adding a shorter alias.

A further requirement follows from unattended scheduling: a scheduler may invoke `wisk start` after a process crash or while a previous run remains incomplete. The runtime must recover from persisted state instead of accumulating orphan scaffolds or requiring process memory.

Handoff continuation adds one more requirement: persisted execution state alone is not enough when the external repository/workspace may have changed since the handoff was created. A resumed session must explicitly revalidate that environment and record the result before relying on stale continuation instructions.

## Design principles

**Defaults encode policy; arguments encode exceptions.**

**Define operations once.** A Wisk operation has one canonical typed definition. CLI and MCP are transport/presentation surfaces, not independent behavioral APIs.

**Persisted state drives execution.** Every state-changing Wisk operation MUST return the next actionable contract state or a terminal state, and that next state MUST be derivable solely from persisted OKF state plus explicit operation inputs and explicitly observed external state required by the contract. Process-local memory must not be required to resume a run.

**External assumptions must be revalidated and documented.** When a run resumes work whose correctness depends on repository/workspace state captured earlier, the revalidation is a contract requirement, not a prompt convention. `wisk check` MUST report it as unsatisfied until the required evidence/check is persisted.

**Handoffs transfer responsibility to evaluate, not an obligation to execute.** A consuming session must account for the transferred intent, but may accept it, reframe it, or reject it when current evidence shows that the proposed continuation is no longer appropriate.

A useful acceptance test is:

> After `wisk init`, can an unattended scheduler invoke only `wisk start` indefinitely, across process restarts, without maintaining a second orchestration prompt or run-local memory, while still forcing stale external assumptions to be revalidated?

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
4. checks persisted state for a compatible live LoopRun;
5. if compatible live work exists, resumes it by recomputing and returning its current actionable state;
6. otherwise, if policy permits a new run, selects the best eligible SessionType;
7. uses Wisk's internal default intent to do the best useful work available in the repository;
8. resolves RunSpec, context policy, and compatible handoff state;
9. creates the live run scaffold when needed;
10. returns the canonical operation envelope including the next actionable state.

The literal default task string is an internal product detail. It must not become consumer configuration or determine every run's human-facing title.

### Explicit task and structural overrides

The task is optional:

```bash
wisk start "Improve CLI ergonomics"
```

RunSpec and SessionType are structural controls and must be named:

```bash
wisk start --session-type wiki
wisk start --run-spec local-review
wisk start "Review current knowledge" --session-type wiki --run-spec local-review
```

The equivalent MCP operation exposes the same fields with the same defaults.

## Start is resumable and idempotent over compatible live work

`wisk start` is not blindly "create a run". It is the idempotent golden-path operation for entering useful work.

If persisted OKF state already contains a compatible live LoopRun, `start` should return that run and its recomputed `next` state rather than create a duplicate.

Compatibility must be determined from persisted, auditable data: selected/pinned SessionType, effective RunSpec, explicit task constraints where relevant, and policy. It must not depend on process-local session state.

`max_parallel` remains authoritative:

- when policy does not permit another compatible parallel run, `start` resumes the existing run;
- when policy permits parallelism and explicit constraints distinguish a new run, creation may proceed;
- ordinary zero-prompt scheduling should prefer resumption over multiplying indistinguishable scaffolds.

If persisted state is ambiguous in a way policy cannot resolve safely, the operation returns `blocked` with structured remediation rather than guessing.

This makes crash recovery, scheduler restarts, and repeated scheduled invocation all use the same operation.

## SessionType override semantics

`--session-type X` is an explicit override.

It bypasses positive eligibility reasons such as interval, threshold, or `on_demand`, and records `selection_reason: explicit-override`.

It does **not** bypass hard blockers such as cooldown, max parallelism, hourly budget, or other safety/resource limits.

`on_demand` remains a scheduling/fallback signal and must not be overloaded to mean explicit user override.

## Canonical operation envelope

Expected domain states are returned through one stable envelope rather than split between successful payloads and generic exceptions.

Conceptually:

```json
{"run":"runs/123","state":"next","next":{"operation":"run_reading","required":["kind","reference","finding"]}}
```

```json
{"run":null,"state":"blocked","blockers":["hourly-budget"],"remediation":[{"action":"retry_later"}]}
```

```json
{"run":"runs/123","state":"done"}
```

The stable state vocabulary begins with:

- `next`: an actionable contract requirement exists;
- `blocked`: expected policy/domain state currently prevents progress;
- `done`: a terminal successful state has been reached.

Expected cadence, eligibility, budget, revalidation, or parallelism states should not be represented as generic `ValueError`. Exceptions remain appropriate for corrupted bundles, invalid persisted invariants, or I/O/runtime failures.

## `next` is a stable contract

The runtime already computes unsatisfied requirements through `check_run`; RFC 0006 promotes that capability into the public operation contract.

Every state-changing operation MUST return either:

- `state: next` plus a structured `next` action;
- `state: blocked` plus structured blockers/remediation; or
- a terminal state such as `done`.

`next` is transport-neutral. A CLI adapter may render a convenient command, but shell text is presentation rather than protocol.

The decisive invariant is:

> `next` MUST be a pure function of persisted OKF state, explicit operation inputs, and any external observation that the persisted contract explicitly requires and records.

A fresh process opening the same initialized repository must be able to recompute the same actionable contract state without hidden state from the process that created the run.

## Handoffs

A compatible pending handoff is execution state, not a reason for the caller to choose another command.

When no compatible live run already exists and policy selects handoff continuation, `wisk start` creates a fresh LoopRun of the target SessionType with the handoff injected into context. It does not reopen the historical run that produced the handoff.

The new LoopRun records the handoff reference and selection reason. The handoff remains active until an outcome successfully accounts for it.

If the resumed LoopRun remains live across a process restart, subsequent `wisk start` invocations resume that live consumer run through the same idempotent-start rule.

When several compatible handoffs exist and the caller supplies no explicit task, selection must be deterministic. The initial policy is oldest compatible active handoff first.

### Handoff goal disposition

A handoff does not force the consuming session to adopt its transferred goals unchanged. It transfers responsibility to evaluate them in current context.

Before the handoff can be considered consumed, the consuming LoopRun MUST record a disposition for each transferred goal. The initial stable dispositions are:

- `accepted`: the consuming session adopts the transferred intent as a current goal;
- `reframed`: the consuming session preserves the underlying intent but replaces the old formulation with a new current goal;
- `rejected`: the consuming session concludes that the transferred goal should not be pursued.

`reframed` and `rejected` MUST be justified by persisted typed reasoning/evidence, such as a `RunDecision`, `RunCheck`, or equivalent domain record. A rejection must never silently erase the historical goal or handoff provenance.

A `rejected` goal may be appropriate when, for example, the repository changed materially, the issue was already resolved, a premise proved false, a proposed approach conflicts with current policy, or evidence shows the work is no longer proportionate/useful.

The historical source goal remains accountable as `carried_forward` because responsibility was transferred at the time of the source run. The consuming run's disposition records what happened to that transferred responsibility afterward; it does not rewrite the historical source run.

A handoff is successfully accounted for when all transferred goals have explicit dispositions and any required resulting goals/decisions are persisted. Only then may the handoff be archived as consumed, reframed, or rejected.

This yields the governing rule:

> Receiving a handoff creates an obligation to evaluate and account for transferred intent, not an obligation to execute it.

`wisk check` MUST treat missing handoff-goal disposition as an unsatisfied lifecycle requirement and surface the appropriate typed `next` action.

## Handoff repository/environment provenance

A handoff carries assumptions about the repository/workspace state in which it was created. Those assumptions MUST be auditable.

A handoff therefore records a minimum environment baseline sufficient to detect material drift. For a Git repository this should include, at minimum:

- commit/HEAD identity at handoff creation;
- branch/ref context when meaningful;
- whether the working tree contained uncommitted changes;
- a stable fingerprint or equivalent provenance for relevant uncommitted state when present.

The baseline is evidence of the state that produced the handoff, not proof that continuation remains safe.

When a later LoopRun consumes a handoff, it MUST perform and persist a revalidation against the current repository/environment before relying on the handoff's prior `state` or `next_action`.

The revalidation should classify at least:

- unchanged baseline;
- compatible forward drift;
- material/divergent drift requiring reassessment;
- unverifiable environment.

The exact Git implementation may evolve, but commit identity should be preferred over timestamps because it carries causal repository history.

## Revalidation is a `wisk check` obligation

Repository/environment revalidation for a resumed handoff is not optional context and must not live only in agent prose.

The consuming LoopRun MUST persist a typed verification record, initially modeled as a `RunCheck` kind such as `handoff-environment` (final name may be chosen during implementation). That check must reference the handoff baseline, record the current observed repository/environment state, classify drift, and state whether the handoff assumptions remain usable or require reassessment.

`check_run()` / `wisk check` MUST understand this as a conditional lifecycle requirement:

- a normal fresh run with no resumed handoff does not owe this check;
- a LoopRun that resumes/consumes a handoff does owe it;
- until the typed revalidation is documented, the run remains incomplete and `next` points to the revalidation requirement;
- if material drift is documented, `next` must require reassessment/update of the continuation plan before stale handoff instructions can be treated as current;
- after environment revalidation, each transferred handoff goal must receive an explicit `accepted`, `reframed`, or `rejected` disposition before the handoff can be consumed;
- a run cannot close successfully while its required handoff-environment revalidation or handoff-goal disposition remains missing/unresolved.

This requirement is lifecycle-derived rather than something every RunSpec author must remember to add manually. RunSpecs may strengthen it, but handoff consumption itself activates the invariant.

In other words, `wisk check` must be able to complain concretely that a resumed handoff has not documented repository/environment verification or has not accounted for its transferred goals.

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
- handoff environment-baseline capture and resumed-run revalidation requirements;
- handoff-goal disposition/accountability;
- RunSpec and context-policy resolution;
- scaffold creation;
- derivation of the next unsatisfied contract requirement from persisted state;
- validation after state transitions;
- structured blockers and remediation;
- actionable guidance through the canonical envelope.

Low-level operations such as run reading, goal, decision, evidence, check, and outcome remain useful primitives. They should participate in the same state envelope and return the newly derived `next`/terminal state after mutation.

## FastMCP and CLI projection

For tool-shaped operations, FastMCP defines the canonical typed public schema.

The CLI projection must preserve operation name, parameter names/types, optionality/defaults, structural named arguments, result semantics, and expected error states.

Machine-readable operation output is canonical. Human-readable CLI presentation may evolve independently as long as semantics remain identical.

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

A distinct `continue` command is not required for the golden path: resumability belongs to `start` plus persisted state.

Session finalization (`finish`) is intentionally outside this RFC because transactional outcome/Experience/Handoff policy deserves a separate lifecycle design.

## Compatibility and migration

Implementation should:

- make task optional in canonical start;
- move positional RunSpec selection to `--run-spec` / named MCP field;
- move positional SessionType selection to `--session-type` / named MCP field;
- preserve unambiguous legacy positional forms for a deprecation window with warnings;
- retain `session start-next` and `wisk_start_next_session` as compatibility aliases during deprecation;
- converge duplicated Cyclopts/FastMCP definitions toward canonical FastMCP tools plus projection/thin adapters;
- promote `check_run`'s next typed action into the stable operation envelope;
- treat expected blockers as typed domain returns rather than generic exceptions;
- make `start` resume compatible persisted live runs before creating duplicates;
- add handoff repository/environment provenance and lifecycle-derived revalidation checks;
- require explicit handoff-goal disposition and evidence for reframe/reject paths;
- keep RFC 0005's supersession annotations current.

## Consumer integration

A consumer installing Wisk in its project environment should reduce a recurring loop to:

```bash
uv run wisk start
```

The scheduler can safely issue that command again after a process restart or on its next cadence tick. Persisted OKF state determines whether Wisk resumes existing work, reports a blocker, requires handoff revalidation/disposition, or creates a new run.

The consumer should not reproduce Wisk's orchestration algorithm in prompts. Domain-specific requirements remain consumer-owned SessionTypes, RunSpecs, context policies, and knowledge.

## Non-goals

This RFC does not:

- remove SessionTypes, RunSpecs, context policies, cadence, or low-level run-state operations;
- allow explicit override to bypass hard blockers;
- make `init` or `upgrade` implicit;
- require `start` to perform arbitrary autonomous shell/GitHub actions;
- archive handoffs at start;
- force a consuming session to accept transferred handoff goals unchanged;
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
8. `start` detects and resumes compatible persisted live work instead of creating an indistinguishable duplicate when policy does not justify another.
9. `max_parallel` participates in resume-vs-create decisions.
10. process restart does not change the derived next actionable state for unchanged persisted state/inputs.
11. compatible handoff continuation creates a fresh consumer run, records the handoff, and leaves it active until the consumer run accounts for it successfully.
12. repeated `start` after handoff-run creation resumes that live consumer run rather than creating another.
13. multiple zero-prompt handoffs are selected deterministically.
14. every handoff records an auditable repository/environment baseline sufficient to detect material drift.
15. every consuming handoff run must persist repository/environment revalidation, and `wisk check` reports it as missing until it exists.
16. material drift forces documented reassessment before stale handoff continuation instructions can be treated as current.
17. every transferred handoff goal receives an explicit `accepted`, `reframed`, or `rejected` disposition before the handoff is consumed.
18. `reframed` and `rejected` dispositions require persisted typed justification/evidence and do not rewrite historical source-run accountability.
19. `wisk check` reports missing handoff-goal disposition as an unsatisfied lifecycle requirement.
20. uninitialized consumer repositories fail clearly rather than falling through to dogfood layout.
21. every state-changing operation returns one canonical envelope with `state` and either `next`, blockers/remediation, or terminal state.
22. expected cadence/eligibility/resource blocking is represented as `state: blocked`, not generic exceptions.
23. `next` is derivable from persisted OKF state, explicit inputs, and contract-required recorded external observations.
24. FastMCP exposes canonical typed operations and the CLI projects/adapts them without semantic drift.
25. `session start-next` / `wisk_start_next_session` are no longer presented as the golden path.
26. RFC 0005 points to RFC 0006 for canonical entrypoint and explicit-start semantics.
27. tests cover zero-prompt start, explicit task, overrides, reasons/blockers, RunSpec pinning, live-run resumption, idempotence, process restart, handoff selection, environment drift/revalidation, handoff goal accept/reframe/reject paths, missing-disposition enforcement, uninitialized repositories, FastMCP/CLI parity, and compatibility behavior.

## Consequence

The architectural change is not merely a shorter command. It is ownership plus recoverability.

A consumer describes what is special about its work. Wisk describes how Wisk operates, persists enough state to recover after interruption, forces stale external assumptions to be revalidated, and requires transferred handoff intent to be explicitly accounted for rather than blindly obeyed. Each public operation is defined once.

Once domain contracts exist, the recurring instruction collapses to:

```bash
wisk start
```

That is the zero-prompt golden path.
