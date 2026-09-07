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

Unattended scheduling adds a stronger requirement: a scheduler may invoke `wisk start` after a process crash or while a previous run remains incomplete. The runtime must recover from persisted state instead of accumulating orphan scaffolds or requiring process-local memory.

Handoff continuation adds another requirement: persisted execution state alone is insufficient when the external repository/workspace may have changed since the handoff was created. A resumed session must revalidate that environment and persist the result before relying on stale continuation instructions.

## Design principles

**Defaults encode policy; arguments encode exceptions.**

**Define operations once.** CLI and MCP are transport/presentation surfaces, not independent behavioral APIs.

**Persisted state drives execution.** Every state-changing Wisk operation MUST return the next actionable contract state or a terminal state. That state MUST be derivable from persisted OKF state, explicit inputs, and explicitly observed external state required and recorded by the contract.

**External assumptions must be revalidated and documented.** When resumed work depends on repository/workspace state captured earlier, revalidation is a contract requirement. `wisk check` MUST report it as unsatisfied until the required typed evidence/check is persisted.

**Handoffs transfer responsibility to evaluate, not an obligation to execute.** A consuming session must account for transferred intent, but may accept, reframe, or reject it when current evidence shows that the proposed continuation is no longer appropriate.

The acceptance question is:

> After `wisk init`, can an unattended scheduler invoke only `wisk start` indefinitely, across process restarts, without maintaining a second orchestration prompt or hidden run-local memory, while still forcing stale external assumptions to be revalidated?

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
) -> OperationResult: ...
```

The runtime/domain layer owns behavior. The canonical operation owns the public typed schema. The CLI may be generated/projected from that schema when practical, or implemented as a thin Cyclopts adapter when terminal-specific UX materially improves usability. A handwritten CLI adapter must delegate to the same operation and must not redefine defaults, selection, errors, or result semantics.

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
2. checks persisted state for a compatible live LoopRun and resumes it when present;
3. evaluates SessionType eligibility, cadence, priority, and blockers when a new run is needed;
4. selects the best eligible SessionType;
5. uses Wisk's internal default useful-work intent;
6. resolves RunSpec, context policy, and compatible handoff state;
7. creates a fresh LoopRun only when needed;
8. returns one canonical operation envelope containing the next actionable state.

The literal default task string is an internal product detail. It must not become consumer configuration or force every zero-prompt run to share the same human-facing title.

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

If persisted OKF state already contains a compatible live LoopRun, `start` returns that run and its recomputed `next` state rather than creating a duplicate.

Compatibility must be determined from persisted, auditable data: selected/pinned SessionType, effective RunSpec, explicit task constraints where relevant, and policy. It must not depend on process-local state.

`max_parallel` remains authoritative. Ordinary zero-prompt scheduling should prefer resumption over multiplying indistinguishable scaffolds. If persisted state is ambiguous in a way policy cannot resolve safely, the operation returns `blocked` with structured remediation rather than guessing.

## SessionType override semantics

`--session-type X` is an explicit override. It bypasses positive eligibility reasons such as interval, threshold, or `on_demand`, and records `selection_reason: explicit-override`.

It does not bypass hard blockers such as cooldown, max parallelism, hourly budget, or other safety/resource limits.

`on_demand` remains a scheduling/fallback signal and must not be overloaded to mean explicit user override.

## Canonical operation envelope

Expected domain states are returned through one stable envelope rather than split between successful payloads and generic exceptions.

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

Every state-changing operation MUST return either `state: next` plus a structured `next` action, `state: blocked` plus structured blockers/remediation, or a terminal state such as `done`.

`next` is transport-neutral. A CLI adapter may render a convenient command, but shell text is presentation rather than protocol.

The decisive invariant is:

> `next` MUST be a pure function of persisted OKF state, explicit operation inputs, and any external observation that the persisted contract explicitly requires and records.

A fresh process opening the same initialized repository must be able to recompute the same actionable contract state without hidden state from the process that created the run.

## Handoffs

A compatible pending handoff is execution state, not a reason for the caller to choose another command.

When no compatible live run exists and policy selects handoff continuation, `wisk start` creates a fresh LoopRun of the target SessionType with the handoff injected into context. It does not reopen the historical run that produced the handoff.

The new LoopRun records the handoff reference and selection reason. The handoff remains active until a later run explicitly accounts for it. Repeated `wisk start` invocations resume the live consumer run.

When several compatible handoffs exist and the caller supplies no explicit task, selection must be deterministic. The initial policy is oldest compatible active handoff first.

### Handoff goal disposition

A handoff does not force the consuming session to adopt its transferred goals unchanged. It transfers responsibility to evaluate them in current context.

The consuming LoopRun must persist a typed disposition. The stable dispositions are:

- `accepted`: adopt the transferred intent as current work;
- `reframed`: preserve the underlying intent but replace the old formulation;
- `rejected`: conclude that the transferred intent should not be pursued.

`reframed` and `rejected` MUST include persisted rationale/evidence. Rejection must never erase the historical goal or provenance.

The governing rule is:

> Receiving a handoff creates an obligation to evaluate and account for transferred intent, not an obligation to execute it.

`wisk check` MUST treat missing or unresolved handoff disposition as an unsatisfied lifecycle requirement.

## Handoff repository/environment provenance

A handoff carries assumptions about the repository/workspace state in which it was created. Those assumptions MUST be auditable.

For a Git repository, the handoff baseline must include at least:

- commit/HEAD identity at handoff creation;
- branch/ref context when meaningful;
- whether the working tree contained uncommitted changes;
- a stable fingerprint or equivalent provenance for relevant uncommitted state when present.

The baseline is evidence of the state that produced the handoff, not proof that continuation remains safe.

A consuming LoopRun MUST revalidate the current repository/environment before relying on the handoff's prior `state` or `next_action`.

The verification should distinguish at least unchanged baseline, compatible forward drift, material/divergent drift requiring reassessment, and unverifiable environment. Commit identity should be preferred over timestamps.

## Revalidation is a `wisk check` obligation

Repository/environment revalidation for a resumed handoff is not optional context and must not live only in agent prose.

The consuming LoopRun MUST persist a typed verification record, initially modeled as a `RunCheck` kind `handoff-environment`. That check references the handoff baseline, records current observed state, classifies drift, and states whether the prior assumptions remain usable or require reassessment.

`check_run()` / `wisk check` MUST treat this as a conditional lifecycle requirement:

- a fresh run without a resumed handoff does not owe the check;
- a handoff-consuming run does owe it;
- until documented, the run remains incomplete and `next` points to revalidation;
- after environment revalidation, `next` points to handoff disposition before ordinary RunSpec work;
- material drift cannot be silently treated as compatible continuation;
- the run cannot close successfully while required revalidation or disposition remains missing or unresolved.

This requirement is lifecycle-derived rather than something every RunSpec author must remember to add manually. RunSpecs may strengthen it.

## Initialized-repository boundary

`wisk start` requires an initialized consumer repository.

Path resolution must not silently reinterpret an uninitialized repository as Wisk's dogfood `knowledge/` layout. Failure should be concise and actionable, directing the caller to `wisk init`.

Dogfood/development layout support may remain only when positively identified. Repository/path overrides may exist at lower layers or through explicit advanced configuration; they are not part of the ordinary golden path.

## Runtime responsibilities

The runtime owns resumable live-run discovery; SessionType eligibility, cadence, priority, blockers, and explicit pinning; compatible handoff continuation; handoff environment-baseline capture and resumed-run revalidation requirements; handoff disposition/accountability; RunSpec and context-policy resolution; scaffold creation; derivation of the next unsatisfied contract requirement; validation after transitions; structured blockers/remediation; and actionable guidance through the canonical envelope.

Low-level operations such as run reading, goal, decision, evidence, check, and outcome remain useful primitives. They participate in the same state envelope and return the newly derived `next` or terminal state after mutation.

## FastMCP and CLI projection

For tool-shaped operations, FastMCP defines the canonical typed public schema. The CLI projection must preserve operation name, parameter names/types, optionality/defaults, structural named arguments, result semantics, and expected error states.

Machine-readable operation output is canonical. Human-readable CLI presentation may evolve independently as long as semantics remain identical.

The target architecture is:

```text
Wisk runtime/domain behavior
          ↑
canonical typed operation
          ↑
FastMCP transport + thin Cyclopts terminal adapter
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
- move RunSpec selection to `--run-spec` / named MCP field;
- move SessionType selection to `--session-type` / named MCP field;
- preserve unambiguous legacy positional forms for a deprecation window where practical;
- retain `session start-next` / `wisk_start_next_session` as compatibility aliases;
- converge duplicated Cyclopts/FastMCP behavior into one shared operation;
- promote `check_run` next action into the stable envelope;
- return expected blockers as typed domain states;
- resume compatible live runs before creating duplicates;
- persist handoff repository/environment provenance;
- make handoff environment revalidation and disposition lifecycle-derived `wisk check` obligations.

Consumer schedulers should invoke only:

```bash
uv run wisk start
```

## Acceptance criteria

RFC 0006 is implemented when:

1. `wisk init` defaults to the current repository;
2. `wisk start` accepts no task and selects useful work;
3. an explicit task remains supported;
4. SessionType and RunSpec overrides are named;
5. repeated `start` over compatible live work resumes rather than duplicates;
6. explicit SessionType override bypasses positive eligibility reasons but honors hard blockers;
7. state-changing operations return a stable `next | blocked | done` envelope;
8. `next` can be recomputed by a fresh process from persisted state;
9. compatible handoff continuation creates a fresh consumer LoopRun rather than reopening historical work;
10. multiple handoffs are selected deterministically;
11. CLI and FastMCP delegate to the same operation semantics;
12. uninitialized consumer invocation fails with actionable guidance rather than silently selecting dogfood state;
13. handoffs persist repository/environment baseline provenance sufficient to detect material drift;
14. every handoff-consuming LoopRun conditionally owes a typed repository/environment revalidation check;
15. `wisk check` reports missing revalidation as unsatisfied and returns it as the next action;
16. after revalidation, `wisk check` requires explicit `accepted | reframed | rejected` handoff disposition before ordinary continuation;
17. documented material drift cannot silently reuse stale continuation assumptions;
18. a resumed run cannot close with missing or unresolved environment revalidation/disposition;
19. bootstrap and consumer documentation advertise `wisk init` once and `wisk start` for ordinary execution.

## Consequence

Wisk persists enough state to resume deterministically and refuses to silently trust external assumptions that may have gone stale. The consumer experience becomes intentionally small: initialize once, then keep calling `wisk start`.
