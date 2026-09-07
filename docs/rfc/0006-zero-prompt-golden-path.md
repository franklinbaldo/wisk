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

`wisk start` means: start the best eligible session and do the best useful work available in this repository.

The user may provide constraints only when they actually intend to override the default:

```bash
wisk start --session-type wiki
wisk start --run-spec local-review
wisk start "Improve CLI ergonomics"
wisk start "Review current knowledge" --session-type wiki
```

The default belongs to Wisk, not to prompts copied into every consumer repository.

This RFC supersedes the operational golden-path entrypoint in RFC 0005. RFC 0005 remains authoritative for the broader consumer/product boundary except where this RFC changes the invocation model.

## Motivation

The current consumer quickstart exposes implementation details:

```bash
wisk init .
wisk session start-next "Do the best useful work available in this repository"
```

Three pieces are unnecessary in the normal case:

1. `.` is already the natural default repository;
2. `session start-next` exposes the scheduler's internal concept of the next eligible session;
3. the generic task text merely restates Wisk's default purpose.

The current CLI also already exposes `wisk start` with positional task, RunSpec, and SessionType arguments. Therefore this RFC is not adding a new command: it is deliberately reshaping an existing public interface. The migration must remove positional ambiguity rather than preserve it accidentally.

There is a second source of duplication today: Wisk separately defines Cyclopts commands and FastMCP tools for the same operations. That duplicates signatures, defaults, descriptions, and potentially behavior. Since FastMCP tools already provide a typed operation schema that can serve agent and command-line callers, the public operation should be defined once and projected into the CLI whenever practical.

## Design principles

**Defaults encode policy; arguments encode exceptions.**

**Define operations once.** A Wisk operation should have one canonical typed definition. CLI and MCP are transport/presentation surfaces, not separate behavioral APIs.

A useful test for the public interface is:

> After `wisk init`, can an unattended scheduler invoke only `wisk start` indefinitely without maintaining a second orchestration prompt?

The answer should be yes.

## Canonical operation surface

FastMCP tools are the canonical typed public operation definitions for Wisk operations that naturally map to MCP tools.

A canonical start operation is conceptually:

```python
@mcp.tool(name="start")
def start(
    task: str | None = None,
    *,
    session_type: str | None = None,
    run_spec: str | None = None,
) -> StartResult:
    ...
```

The precise implementation may delegate immediately into the Wisk runtime/domain layer, but there must not be a second independently specified CLI signature with different defaults or semantics.

The CLI should be generated or projected from the canonical FastMCP tool schema when FastMCP can express the intended terminal UX faithfully. Wisk may keep a thin handwritten CLI adapter only where terminal-specific interaction materially improves usability and cannot be represented cleanly by the tool schema. Such an adapter must delegate to the same canonical operation and must not redefine behavior.

Cyclopts therefore remains an implementation detail available for CLI projection and exceptional terminal UX, not a second source of truth for the API.

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

1. resolves the initialized consumer repository from the current working directory;
2. evaluates SessionType eligibility, cadence, priority, and blockers;
3. selects the best eligible SessionType;
4. uses the standard internal work intent: do the best useful work available in the repository;
5. resolves the applicable RunSpec and context policy;
6. resolves whether an active compatible handoff should be continued;
7. creates the live run scaffold before substantive work;
8. returns actionable execution context.

The exact default task string is an internal product default. It should not become consumer configuration merely because the runtime needs a value internally.

### Explicit task

```bash
wisk start "Improve CLI ergonomics"
```

The task is optional. Supplying it constrains the work while ordinary SessionType selection remains in effect unless the caller also provides an explicit override.

### Named structural overrides

RunSpec and SessionType are structural controls and therefore must be named flags, not additional positional arguments:

```bash
wisk start --session-type wiki
wisk start --run-spec local-review
wisk start "Review current knowledge" --session-type wiki --run-spec local-review
```

This removes the current positional ambiguity between free-form task text and structural identifiers.

The equivalent MCP call exposes the same fields with the same defaults. No translation layer may silently reinterpret them.

## SessionType override semantics

`--session-type X` is an explicit override.

The override bypasses positive eligibility reasons such as interval, threshold, or `on_demand`. The resulting selection records `selection_reason: explicit-override`.

The override does **not** bypass blockers such as:

- cooldown;
- max parallelism;
- hourly budget;
- other hard safety/resource blockers introduced by policy.

In other words, the caller may say "start this type even though it is not due" but not "ignore runtime safety and resource limits".

`on_demand` must not be overloaded for this behavior. It remains a scheduling/fallback signal. A SessionType may have `on_demand: false` and still be explicitly startable by id.

This preserves the semantics already present in the runtime, where explicit SessionType pinning is distinct from cadence-driven selection, while making the distinction auditable and explicit in the public contract.

## Inspection remains separate

```bash
wisk session next
```

The distinction is intentional:

- `wisk start` expresses user intent: start useful work;
- `wisk session next` exposes scheduler state for inspection/debugging.

The golden path should not require the caller to turn the result of `next` into a separate `start-next` operation.

Whether `session next` itself remains handwritten CLI, becomes a projected tool, or is renamed later is outside this RFC. Its behavior must still come from one canonical operation.

## Handoffs

A compatible pending handoff is execution state, not a reason for the caller to choose another command.

When policy selects continuation, `wisk start` starts a **fresh LoopRun of the target SessionType with the handoff injected into context**. It does not reopen or mutate the previous LoopRun.

The new LoopRun records the handoff reference, for example as `resumed_handoff`, and records why continuation was selected.

The handoff is **not archived at start**. It remains active until the new run reaches an outcome that successfully consumes or supersedes it. This prevents a failed or interrupted resumed run from losing the recovery path.

When multiple compatible handoffs exist and the caller supplied a task, existing relevance ordering may be used. In zero-prompt execution, where no explicit task exists, selection must be deterministic. The initial policy is oldest compatible active handoff first. A later RFC may introduce explicit Handoff priority without changing the `wisk start` contract.

Explicit handoff inspection and continuation commands remain available for debugging and manual control.

## Run identity under zero-prompt

The internal default task must not cause every zero-prompt run to receive the same slug and title.

When no task is supplied:

- the run title should be derived from the selected SessionType and resolved work/context rather than from the literal default task string;
- generated slugs must remain deterministic enough for auditability and unique enough to avoid meaningless suffix churn;
- the effective default intent should still be recorded separately from the human-facing run title.

## Initialized-repository boundary

`wisk start` must require an initialized consumer repository.

Path resolution must not silently reinterpret an uninitialized consumer repository as Wisk's dogfood `knowledge/` layout. If the current repository has not been initialized, `start` should fail with a concise actionable message directing the caller to `wisk init`.

Dogfood/development layout resolution may remain available only when the runtime can positively identify that layout rather than by fallback.

## Runtime responsibilities

Zero-prompt does not mean zero contract. It means moving orchestration knowledge to the component that owns it.

The underlying start operation should progressively own the normal-case decisions for:

- SessionType eligibility, cadence, priority, and explicit pinning;
- compatible handoff continuation;
- RunSpec resolution;
- context-policy resolution;
- run-scaffold creation before substantive execution;
- discovery of the next unsatisfied contract requirement;
- validation after state transitions;
- actionable guidance about readings, evidence, checks, and completion.

Low-level operations such as run reading, goal, decision, evidence, check, and outcome remain valuable primitives and debugging/automation interfaces. Their existence should not require consumer prompts to reproduce Wisk's execution algorithm.

## FastMCP and CLI projection

FastMCP is not merely an alternate transport for a separately designed CLI. For operations that map naturally to tools, the FastMCP tool schema is the canonical public schema.

The projected CLI must preserve:

- operation name;
- parameter names and types;
- optionality and defaults;
- named-vs-positional intent;
- descriptions/help semantics where supported;
- result semantics and error conditions.

A handwritten Cyclopts command is acceptable only as a thin presentation adapter when generated/projection behavior cannot deliver the intended terminal UX. It must call the same canonical operation and should be covered by parity tests.

The architecture should therefore be:

```text
Wisk runtime/domain behavior
          ↑
canonical typed FastMCP operations
          ↑
MCP transport + CLI projection/thin terminal adapters
```

and not:

```text
Wisk runtime
   ↑        ↑
CLI API   MCP API
```

where each surface independently specifies the operation.

The current duplicated `wisk start` / `wisk_start` and `session start-next` / `wisk_start_next_session` surfaces should converge during implementation of this RFC.

## Lifecycle

Bootstrap, execution, and managed-bundle upgrade are separate operations:

```bash
wisk init       # first adoption
wisk start      # ordinary execution
wisk upgrade    # explicit managed-bundle refresh
```

`start` must not implicitly run `init` or `upgrade`.

## Compatibility and migration

This RFC changes an existing `wisk start` signature rather than adding a wholly new entrypoint, and it changes the ownership model of the CLI/MCP definitions.

Migration should therefore be explicit:

- make task optional in the canonical start operation;
- make repository arguments default to the current directory where appropriate;
- move positional RunSpec selection to `--run-spec` / the equivalent named MCP field;
- move positional SessionType selection to `--session-type` / the equivalent named MCP field;
- preserve the old positional `start <task> [run_spec] [session_type]` form for a deprecation window when it can be parsed unambiguously, with a clear warning;
- retain `wisk session start-next <task>` and `wisk_start_next_session` as compatibility aliases with deprecation notices;
- migrate duplicated Cyclopts/FastMCP operation definitions toward canonical FastMCP tools plus CLI projection/thin adapters;
- update README and consumer guidance to use `wisk init` once and `wisk start` thereafter;
- retain the supersession note in RFC 0005's golden-path and explicit-start sections.

A later release may remove deprecated positional structural arguments, `session start-next`, and redundant handwritten CLI adapters where the generated/projected CLI is sufficient.

## Consumer integration

A consumer that installs Wisk in its project environment should be able to reduce a recurring agent loop to the environment-specific launcher plus `wisk start`.

For example, with uv:

```bash
uv run wisk start
```

The consumer should not need another prompt saying to inspect issues, choose a SessionType, run checks, synthesize knowledge, or evolve skills when those behaviors are represented by Wisk contracts and policy.

Domain-specific requirements still belong in consumer-owned SessionTypes, RunSpecs, context policies, and knowledge. Zero-prompt removes duplicated orchestration, not domain specialization.

## Output contract

The canonical start operation should return enough structured information for an agent or projected CLI to act without reconstructing orchestration from documentation. At minimum:

- selected SessionType;
- `selection_reason` (`cadence`, `on-demand-fallback`, `explicit-override`, `handoff-continuation`, or equivalent stable vocabulary);
- resolved RunSpec;
- run artifact/reference;
- effective task/intention;
- human-facing run title;
- resumed handoff reference when applicable;
- blockers when an explicit override is rejected;
- actionable next contract requirement or execution guidance.

Machine-readable operation output is canonical. Human-readable CLI presentation may evolve independently as long as it does not change operation semantics.

## Non-goals

This RFC does not:

- remove SessionTypes, RunSpecs, context policies, or cadence;
- make all repositories use identical domain policy;
- remove low-level run-state operations;
- allow explicit override to bypass hard blockers;
- require `start` to perform arbitrary autonomous shell or GitHub actions itself;
- make `init` or `upgrade` implicit mutations of `start`;
- reopen old LoopRuns when continuing a handoff;
- overload `on_demand` to mean explicit user override;
- require every possible terminal interaction to be generated from FastMCP when a thin terminal-specific adapter is demonstrably better.

## Acceptance criteria

The RFC is implemented when all of the following are true:

1. `wisk init` initializes the current repository without requiring `.`.
2. `wisk start` works with no task argument.
3. no-task execution uses Wisk's standard useful-work intent without deriving every run title from that literal string.
4. `wisk start "task"` supports an explicit task.
5. `wisk start --session-type <type>` bypasses eligibility reasons, records `explicit-override`, and still honors blockers.
6. `wisk start --run-spec <id>` pins RunSpec explicitly.
7. ordinary selection remains driven by eligibility, cadence, and priority when no override is supplied.
8. compatible handoff continuation creates a fresh run, records the handoff reference, and does not archive the handoff until successful outcome.
9. multiple zero-prompt handoffs are selected deterministically.
10. an uninitialized consumer repository fails clearly instead of falling through to dogfood layout.
11. FastMCP exposes the canonical typed start operation with optional task and named structural overrides.
12. the CLI is generated/projected from that canonical operation where practical, or uses only a thin parity-tested adapter where terminal-specific UX requires it.
13. CLI and MCP expose identical start semantics, defaults, errors, and output meaning.
14. `session start-next` and `wisk_start_next_session` are no longer presented as the golden path.
15. RFC 0005 explicitly points to RFC 0006 for the canonical entrypoint and explicit-start semantics.
16. bootstrap, normal execution, and upgrade are documented as distinct lifecycle operations.
17. tests cover default start, explicit task, SessionType override reasons/blockers, RunSpec override, handoff continuation, uninitialized repositories, generated/projected CLI parity, MCP parity, selection behavior, and compatibility behavior.

## Consequence

The important architectural change is not the shorter command. It is ownership.

A consumer should describe what is special about its work. Wisk should describe how Wisk operates. Wisk should also define each public operation once rather than separately for humans and agents.

Once the repository has encoded its domain-specific contracts, the recurring instruction should collapse to:

```bash
wisk start
```

That is the zero-prompt golden path.