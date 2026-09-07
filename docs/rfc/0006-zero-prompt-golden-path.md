# RFC 0006: Zero-prompt golden path

- Status: Proposed
- Date: 2026-09-07

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

The user may override the selected session type or provide a task when they actually intend to constrain execution:

```bash
wisk start --session-type wiki
wisk start "Improve CLI ergonomics"
wisk start "Review the current knowledge" --session-type wiki
```

The default belongs to Wisk, not to prompts copied into every consumer repository.

## Motivation

The current consumer quickstart exposes implementation details:

```bash
uvx wisk init .
wisk session start-next "Do the best useful work available in this repository"
```

Three pieces of that interface are unnecessary in the normal case:

1. `.` is already the natural default repository;
2. `session start-next` exposes the scheduler's concept of a next eligible session;
3. the generic task text merely restates Wisk's default purpose.

When every consumer repeats those details in an hourly prompt or agent instruction, Wisk is not fully owning its orchestration contract. The repeated prompt can drift from the runtime and forces consumers to understand concepts that should remain implementation details.

The CLI should make the common intent implicit and expose controls only as overrides.

## Design principle

**Defaults encode policy; arguments encode exceptions.**

If Wisk already knows the normal repository, normal work intent, eligible SessionTypes, cadence, priority, context policy, and RunSpec resolution, the caller should not repeat them.

A useful test for the public CLI is:

> After `wisk init`, can an unattended scheduler invoke only `wisk start` indefinitely without maintaining a second orchestration prompt?

This RFC proposes that the answer should be yes.

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

1. resolves the repository from the current working directory;
2. evaluates eligible SessionTypes, cadence, priority, and local policy;
3. selects the best eligible SessionType;
4. uses the standard work intent: do the best useful work available in the repository;
5. resolves the applicable RunSpec and context policy;
6. creates the live run scaffold before substantive work;
7. returns the actionable execution context for that run.

The exact default task string is an internal product default. It should not become consumer configuration merely because the CLI needs a value internally.

### Explicit task

A caller may constrain the work:

```bash
wisk start "Improve CLI ergonomics"
```

The task is optional. Supplying it replaces the generic work intent; it does not bypass normal SessionType selection unless policy says that a requested task makes a particular type ineligible.

### SessionType override

A caller may explicitly select a SessionType:

```bash
wisk start --session-type experience
wisk start --session-type wiki
wisk start --session-type skill
```

`--session-type` is an override, not part of the ordinary golden path. Session type is deliberately a named flag rather than a positional argument so it cannot be confused with free-form task text.

The runtime should validate that the requested type exists and report clearly when policy prevents it from starting. Whether an explicit override may bypass cadence eligibility should be an explicit policy decision rather than an accidental consequence of CLI parsing.

### Inspection remains separate

Commands that inspect scheduling without starting work remain useful:

```bash
wisk session next
```

The distinction is intentional:

- `wisk start` expresses user intent: start useful work;
- `wisk session next` exposes scheduler state for inspection/debugging.

The public golden path should not require the caller to turn the result of `next` into a separate `start-next` operation.

## Runtime responsibilities

Zero-prompt does not mean zero contract. It means moving orchestration knowledge to the component that owns it.

`wisk start` should progressively own the following normal-case decisions:

- SessionType eligibility, cadence, and priority;
- continuation of a compatible high-priority handoff when policy calls for it;
- RunSpec resolution;
- context-policy resolution;
- creation of the run scaffold before substantive execution;
- discovery of the next unsatisfied contract requirement;
- validation after state transitions;
- actionable guidance about required readings, evidence, checks, and completion.

Low-level commands such as `run reading`, `run goal`, `run decision`, `run evidence`, `run check`, and `run outcome` remain valuable primitives and debugging/automation interfaces. Their existence should not require consumer prompts to reproduce Wisk's execution algorithm.

## Handoffs

A pending compatible handoff is execution state, not a reason for the caller to choose another command.

When policy considers a handoff the highest-priority continuation, `wisk start` should resume it automatically. Explicit handoff inspection and continuation commands remain available for debugging and manual control.

The selection must remain auditable: the resulting run should record why continuation was chosen over a fresh eligible session.

## Upgrade lifecycle

Bootstrap, execution, and managed-bundle upgrade are separate operations:

```bash
wisk init       # first adoption
wisk start      # ordinary execution
wisk upgrade    # explicit managed-bundle refresh
```

`start` must not require callers to run `init` on every invocation. If Wisk has not been initialized, it should fail with a concise actionable message rather than silently modifying the repository.

## Consumer integration

A consumer that installs Wisk in its project environment should be able to reduce a recurring agent loop to the environment-specific launcher plus `wisk start`.

For example, with uv:

```bash
uv run wisk start
```

The consumer should not need an additional prompt saying to inspect issues, choose a SessionType, run checks, synthesize knowledge, or evolve skills when those behaviors are already represented by Wisk contracts and policy.

Domain-specific requirements still belong in consumer-owned SessionTypes, RunSpecs, context policies, and knowledge. Zero-prompt removes duplicated orchestration, not domain specialization.

## Compatibility and migration

Initially:

- make the task argument to the existing start path optional;
- make repository arguments default to `.` where appropriate;
- introduce `wisk start` as the canonical entry point;
- retain `wisk session start-next <task>` as a compatibility alias with a deprecation notice;
- update README and consumer guidance to use `wisk init` once and `wisk start` thereafter.

A later release may remove `session start-next` after the normal deprecation window.

Existing explicit-task automation continues to work through `wisk start "task"`.

## CLI output

`wisk start` should return enough structured information for an agent to act without reconstructing orchestration from documentation. At minimum the result should identify:

- selected SessionType and why it was selected;
- resolved RunSpec;
- run artifact/reference;
- effective task/intention;
- whether a handoff was resumed;
- actionable next contract requirement or execution guidance.

Machine-readable output should remain stable enough for agent launchers while human-readable presentation can evolve independently.

## Non-goals

This RFC does not:

- remove SessionTypes, RunSpecs, context policies, or cadence;
- make all repositories use identical domain policy;
- remove low-level run-state commands;
- require `start` to perform arbitrary autonomous shell or GitHub actions itself;
- make `init` or `upgrade` implicit mutations of `start`;
- define the final policy for whether `--session-type` bypasses cadence.

## Acceptance criteria

The RFC is implemented when all of the following are true:

1. `wisk init` initializes the current repository without requiring `.`.
2. `wisk start` works with no task argument.
3. no-task execution uses Wisk's standard useful-work intent.
4. `wisk start "task"` supports an explicit task.
5. `wisk start --session-type <type>` supports an explicit SessionType override with clear policy semantics.
6. ordinary selection remains driven by eligibility, cadence, and priority when no override is supplied.
7. a consumer scheduler can invoke only `wisk start` after initialization.
8. `session start-next` is no longer presented as the golden path.
9. bootstrap, normal execution, and upgrade are documented as distinct lifecycle operations.
10. tests cover default start, explicit task, SessionType override, uninitialized repositories, selection behavior, and compatibility behavior.

## Consequence

The important architectural change is not the shorter command. It is ownership.

A consumer should describe what is special about its work. Wisk should describe how Wisk operates. Once the repository has encoded its domain-specific contracts, the recurring instruction should collapse to a single intent:

```bash
wisk start
```

That is the zero-prompt golden path.