---
type: ConceptSpecification
concept_type: RunExecution
description: "Objective subprocess execution observed by Wisk inside a LoopRun."
---

# Concept: RunExecution

A `RunExecution` records one real command invocation that Wisk itself attempted and observed. It is a raw execution fact, not a claim that the command proved an assertion, satisfied a check, or produced reusable knowledge.

`RunExecution` belongs to the same Raw Layer graph as the other `Run*` children. Semantic records may reference it, but execution and interpretation remain distinct.

## Required Frontmatter Fields

- `type`: `"RunExecution"`
- `id`: unique execution identifier
- `run`: owning `LoopRun`
- `executor`: executor mode; `"argv"` for the 0.4 RC direct-process golden path
- `argv`: exact argument vector passed to the process launcher
- `cwd`: working directory used for the invocation
- `started_at`: measured invocation start timestamp
- `finished_at`: measured invocation finish timestamp
- `stdout_bytes`: observed stdout byte count
- `stderr_bytes`: observed stderr byte count
- `stdout_digest`: SHA-256 digest of stdout bytes
- `stderr_digest`: SHA-256 digest of stderr bytes

## Optional Frontmatter Fields

- `exit_code`: process exit code when the process launched successfully
- `launch_error`: concise launcher error when the process could not be started
- `why`: concise caller-declared purpose captured before execution
- `expect`: concise caller-declared observable expectation captured before execution
- `next_before`: active typed next requirement before execution
- `next_after`: active typed next requirement after projections and re-check
- `git_head_before`: Git HEAD observed before execution when available
- `git_dirty_before`: Git dirty state observed before execution when available
- `git_head_after`: Git HEAD observed after execution when available
- `git_dirty_after`: Git dirty state observed after execution when available

Duration is derived from `started_at` and `finished_at`.

Wisk does not persist the full process environment by default. Command output retention is policy-driven; the core record preserves counts and stable digests without requiring full logs to be committed.

A zero exit code is only an execution result. `RunEvidence`, `RunCheck`, `RunObservation`, and `RunSkillUse` remain explicit semantic projections with their own contracts.
