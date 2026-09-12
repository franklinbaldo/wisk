---
type: ConceptSpecification
concept_type: RuntimeRFC
title: "RFC 0003 — Runtime execution protocol and `wisk run` golden path"
status: proposed
updated: 2026-09-08
target_release: "0.4.0rc1"
depends_on:
  - "RFC 0006 — zero-prompt start/resume semantics"
  - "RFC 0007 — Work traces as the Raw Layer"
---

# RFC 0003 — Runtime execution protocol and `wisk run` golden path

## Summary

Wisk should make the observable path through an agent run easy without making it mandatory.

The canonical runtime protocol is:

```text
start(...)  -> resolve or create the active LoopRun + next
run(...)    -> execute real argv + persist RunExecution + optional typed projections + next
record(...) -> persist a typed Run* fact that was not naturally captured by run + next
check(run)  -> authoritative structural/semantic diagnostics + next
trace(run)  -> reconstruct the queryable run graph
```

`wisk run` is the ergonomic execution golden path. It really executes the requested command. It is not a logger pretending that a command ran, and it is not a second orchestration mode beside `LoopRun`, `SessionType`, `RunSpec`, `next`, and `check`.

RFC 0007 establishes that a Work `LoopRun` plus its typed child records is Wisk's Raw Layer. This RFC defines how real command execution enters that graph.

The central rule is:

> **Execution facts are captured automatically; semantic meaning is projected into typed records only when the active contract makes the mapping deterministic or the caller declares the relationship explicitly.**

Therefore:

- `wisk run` always knows that a process ran, with which argv, in which directory, for how long, with which exit code, and against which repository state;
- it must not infer that an arbitrary successful command satisfied `RunEvidence`, `RunCheck`, `RunObservation`, or another semantic requirement merely because the process exited zero;
- explicit flags can ask `wisk run` to materialize command-bound typed records such as evidence, checks, observations, and skill-use provenance;
- `wisk record` remains the secondary path for typed facts that are not naturally command executions;
- externally executed work remains valid: `check` judges the resulting run state, not whether every action passed through Wisk.

This gives Wisk observability without turning it into a compulsory shell wrapper.

## Relationship to the 0.4 learning model

RFC 0007 pivots the canonical learning cycle to:

```text
Worker
  ↓
Work LoopRun + Run* children       ← Raw Layer
  ↓
Wiki Maintainer
  ↓
WikiEntry                          ← Wiki Layer
  ↓
Skill Evolver
  ↓
SkillProposal / AgentSkill         ← Skills Layer
```

Ordinary agent providers already retain rich transient execution context while a session is alive, but that context is normally not deposited in the repository as structured, queryable execution history.

`wisk run` helps close that gap. It makes command execution itself a first-class child of the active `LoopRun`, so a later Wiki Maintainer can distinguish facts such as:

- what command was actually run;
- whether the Worker expected it to pass or fail;
- whether it did;
- what repository state existed before and after;
- which skill version guided the action;
- which execution was later promoted to evidence or a formal check;
- which observations were explicitly recorded while context was still hot.

The command wrapper does not replace `RunGoal`, `RunDecision`, `RunEvidence`, `RunCheck`, `RunObservation`, `RunSkillUse`, or `RunOutcome`. It supplies objective execution facts and an ergonomic way to connect those facts to the semantic graph.

## Decision 1 — `wisk run` owns real command execution

The preferred CLI form is:

```bash
wisk run \
  --why "Verify the parity fix" \
  --expect "The focused regression test passes" \
  -- uv run pytest tests/test_parity.py -q
```

Everything after `--` is treated as argv and executed directly.

Wisk must not inject an implicit shell. In particular, shell expansion, pipelines, redirection, globbing, command substitution, and environment interpolation must not happen merely because the command string contains shell syntax.

If Wisk later supports shell execution, that must be an explicit separate choice such as `--shell`, with the resulting executor mode persisted in the execution record.

The direct-argv form is the golden path because it is reproducible, does not depend on hidden shell parsing, and makes the observed command unambiguous.

### Start/resume integration

`wisk run` should compose with RFC 0006 rather than requiring a separate preparatory ritual.

Its high-level flow is:

```text
1. resolve the target LoopRun
   - explicit --run wins;
   - otherwise call the canonical idempotent start/resume operation;
   - optional --task / --session-type / --run-spec feed that operation.

2. call check(run) and preserve next_before.

3. capture repository/process pre-state.

4. execute argv for real.

5. capture repository/process post-state and persist RunExecution.

6. materialize any explicitly requested typed projections.

7. call check(run) again and return next_after.
```

`run` therefore advances the same state machine as all other Wisk operations. It does not own a separate lifecycle.

## Decision 2 — command execution gets its own raw record

RFC 0007's Raw Layer should gain a first-class command-execution child:

```text
LoopRun
├── RunReading*
├── RunGoal*
├── RunDecision*
├── RunExecution*       ← this RFC
├── RunEvidence*
├── RunCheck*
├── RunObservation*
├── RunSkillUse*
└── RunOutcome
```

The concept should be named `RunExecution`, not `Experience` and not `RunEvidence`.

A process having executed is an objective fact. Whether that execution constitutes evidence for a claim, verifies a contract, demonstrates friction, or exercises a skill is a separate semantic statement.

A minimal `RunExecution` should preserve:

```yaml
type: RunExecution
id: run-executions/...
run: runs/...
executor: argv
argv:
  - uv
  - run
  - pytest
  - tests/test_parity.py
  - -q
cwd: /workspace/causaganha
started_at: 2026-09-08T19:45:00Z
finished_at: 2026-09-08T19:45:02Z
exit_code: 0
why: "Verify the parity fix"
expect: "The focused regression test passes"
next_before: "check:tests"
next_after: "outcome"
stdout_digest: sha256:...
stderr_digest: sha256:...
```

Repository-aware runtimes should additionally preserve objective Git state when available:

```yaml
git_head_before: abc123...
git_dirty_before: true
git_head_after: abc123...
git_dirty_after: true
```

A later implementation may normalize repository provenance into a reusable environment/snapshot concept. The RC does not need that abstraction before the execution facts are useful.

### Timing

`started_at` and `finished_at` are measured by the runtime. Duration is derived.

The model must not estimate execution time.

### Environment and secrets

Wisk must not persist the full process environment by default. Environment variables routinely contain credentials and other secrets.

Only explicit allowlisted environment metadata or values already represented by a safe runtime contract may be persisted.

## Decision 3 — stdout/stderr are observable but not blindly versioned

Command output is useful raw evidence but can be huge, noisy, binary-adjacent, or secret-bearing.

The default contract should therefore separate **observation** from **full retention**:

- stream stdout/stderr normally to the caller;
- calculate byte counts and stable digests;
- preserve bounded text excerpts only under an explicit output policy;
- persist a durable artifact reference when the active policy chooses to retain full output;
- record whether output was truncated, omitted, or retained elsewhere.

A successful `wisk run` must not require committing megabytes of test logs into Git merely to prove that pytest ran.

When an output fragment materially supports later reasoning, the caller can project the execution into `RunEvidence` with an appropriate concise summary/reference.

## Decision 4 — keep `--why` and `--expect`, but give them narrow semantics

`--why` and `--expect` are useful because they preserve information that disappears quickly after the command runs.

They are deliberately **not** chain-of-thought capture.

### `--why`

`--why` is a concise declared purpose for this command:

```bash
--why "Confirm the suspected NULL/empty-string divergence before changing code"
```

It answers: *why is this command being run now?*

It does not satisfy a `RunDecision` or `RunGoal` requirement by itself. Consequential choices and session goals remain typed records with their own contracts.

### `--expect`

`--expect` is a concise, observable pre-execution expectation:

```bash
--expect "Exactly one parity test fails because SQL returns NULL"
```

It answers: *what observable result does the Worker expect before seeing the output?*

This is particularly valuable for TDD and investigation because it distinguishes prediction from post-hoc explanation.

A mismatch between `expect` and the observed result may later justify a `RunObservation(kind: surprise)`, but Wisk must not manufacture that semantic conclusion automatically unless the comparison is machine-deterministic or the caller explicitly requests the observation.

Neither flag is mandatory. They are cheap metadata with high learning value when the intent or expected outcome would otherwise be lost.

## Decision 5 — command-bound semantic records can be requested as projections

Most agent actions should not require a separate `wisk record ...` command after every process invocation.

`wisk run` should therefore support explicit projection flags for semantic facts that are naturally coupled to the command it is about to execute.

The exact option parser is an implementation detail, but the 0.4 contract should support the following semantics.

### Evidence projection

```bash
wisk run \
  --why "Reproduce the regression" \
  --expect "The regression test fails before the fix" \
  --evidence red-test \
  -- uv run pytest tests/test_parity.py -q
```

The command always creates `RunExecution`.

Because the caller explicitly declares `--evidence red-test`, Wisk additionally creates a `RunEvidence(kind: red-test)` whose reference points to the `RunExecution` and whose factual summary is derived from the observed command result.

The generated summary should stay objective, for example:

```text
`uv run pytest tests/test_parity.py -q` exited 1; captured output digest sha256:....
```

The wrapper should not invent a domain conclusion beyond what the execution proves.

### Check projection

```bash
wisk run \
  --why "Verify the implementation" \
  --expect "The regression test passes" \
  --check tests \
  -- uv run pytest tests/test_parity.py -q
```

Because `--check tests` explicitly declares that this command is being used as a formal check, Wisk may deterministically map process success to the `RunCheck` status:

```text
exit code 0     -> pass
non-zero exit   -> fail
execution error -> inconclusive/error according to the check contract
```

The generated `RunCheck.procedure` records the argv, and its result records the observed exit status/output reference.

If `RunCheck.evidence` requires a `RunEvidence`, the wrapper should create or reuse an execution-backed `RunEvidence` and link the check to it. The fact that the command ran remains in `RunExecution`; the evidence record is the semantic projection used by the check graph.

A TDD RED run should normally use `--evidence red-test`, not `--check tests`, because an intentionally failing test is useful evidence but does not mean the test check has passed.

### Observation projection

Some observations are obvious only while the command context is hot. Wisk may support an explicit form such as:

```bash
wisk run \
  --observe friction \
  --note "The generator scans the entire catalog for a one-row validation" \
  -- uv run python scripts/reproduce.py
```

This creates `RunObservation(kind: friction)` linked to the active run and, where the schema permits, to the `RunExecution` that prompted it.

Observation text is caller-declared. Wisk should not infer subjective categories such as friction, surprise, near-miss, or workaround solely from exit status.

### Skill-use projection

When a particular skill actually guides an execution, the caller should be able to preserve that provenance without a second command:

```bash
wisk run \
  --using skill-audit-duplicated-domain-logic@1.2.0 \
  --why "Search for another local reimplementation of the classifier" \
  -- rg "classify_|classification" src scripts
```

`--using` creates or reuses the run-scoped `RunSkillUse` after validating the requested skill/version against the installed Wisk knowledge.

Merely having a skill in context must not count as use. The provenance claim is that the Worker actually exercised that procedure.

### Repeatability

Projection flags should be repeatable where that is meaningful. One execution may support more than one evidence kind or formal check, but implementations should prefer a small number of meaningful relationships over generating metadata mechanically.

## Decision 6 — `wisk record` becomes the explicit typed-write namespace

The 0.3 CLI used `wisk run reading`, `wisk run goal`, `wisk run evidence`, `wisk run check`, and related subcommands as the manual typed-write surface.

That naming now conflicts with the much more natural meaning of `wisk run`: execute work.

For 0.4, the command namespace should become:

```text
wisk run -- <argv>            # execute a real command

wisk record reading ...       # explicit typed writes
wisk record goal ...
wisk record decision ...
wisk record evidence ...
wisk record check ...
wisk record observation ...
wisk record skill-use ...
wisk record outcome ...

wisk check [run]
wisk trace [run]
```

The old `wisk run <record-type>` forms may remain temporary compatibility aliases during the RC, but new documentation and agent guidance must teach `record`.

`record` is intentionally secondary to `run` for command-bound facts. It remains necessary because not every important run fact is a subprocess:

- a goal is declared before work;
- a consequential architectural choice may be a `RunDecision`;
- a reading may come from an MCP/API/document source rather than a local command;
- a handoff may describe unfinished responsibility;
- an externally executed action may need evidence/check records even though Wisk did not execute it;
- an outcome closes the run rather than representing one process invocation.

Every typed write should return the newly derived `next` by re-running the same authoritative check logic.

## Decision 7 — `check` remains the authority

`wisk run` is the golden path, not the law.

An agent may legitimately work through:

- another shell;
- an IDE;
- a cloud computer;
- a GitHub connector;
- an MCP tool;
- a CI runner;
- a browser;
- another application that Wisk cannot directly wrap.

Those actions do not make the run invalid.

The conformance question is always:

> Does the persisted repository state and its typed run graph satisfy the active `SessionType`, `RunSpec`, lifecycle rules, and normative OKF schemas?

That is answered by `check`.

External execution may require explicit `wisk record evidence`, `record check`, `record observation`, or another typed write because Wisk cannot truthfully create a `RunExecution` for a process it did not observe.

Wisk must never pretend to have executed or captured a command merely because the caller reports that it happened.

## Decision 8 — `next` informs execution but does not become a hidden gate

Before executing a command, `wisk run` captures the current typed `next` from `check`.

After the command and requested projections are persisted, it captures the new `next`.

This makes a single invocation self-explanatory:

```text
next_before: check:tests
command: uv run pytest -q
exit_code: 0
next_after: outcome
```

When the command does not obviously correspond to the current `next`, Wisk may expose that fact to the caller, but should not reject the execution by default.

Agents often need to investigate, recover from errors, or intentionally deviate from the simplest next action. `--why` is a cheap way to make a material deviation legible when useful.

Only an explicit active contract may turn a particular action or artifact into a mandatory gate.

## Decision 9 — process result and Wisk persistence failures are distinct

A command may have real side effects even if Wisk later fails to persist its metadata.

The runtime must preserve this distinction.

If the subprocess starts, Wisk must never report the operation as though nothing happened merely because a later schema write, disk write, or validation step failed.

The error surface should make at least these facts available:

```text
command_started: true|false
command_exit_code: <int|null>
execution_record_persisted: true|false
effect_may_have_occurred: true|false
```

The CLI should normally return the wrapped command's exit code when capture/persistence succeeds.

If Wisk itself fails after the command executed, it should return a Wisk failure while surfacing the original command result and clearly stating that external effects may already have occurred.

This is important for commands such as migrations, commits, deploys, publication, issue/PR mutation, or any other non-idempotent action.

## Decision 10 — FastMCP is capability-aware, not imaginary

CLI and MCP should share the same semantic operations, but they do not necessarily have the same execution capability.

A FastMCP server may expose real command execution only when it has an authorized repository environment in which it can actually spawn the argv and observe its result.

If the MCP server cannot execute in the caller's environment, it must not expose a fake `run` that accepts reported stdout/exit code and writes a `RunExecution` as though Wisk observed it.

In that environment, the supported path is:

```text
external tool executes
→ caller records the truthful typed facts Wisk can know
→ check remains authoritative
```

Capability discovery should make that distinction explicit.

## Golden paths

### Ordinary verification

```bash
wisk start

wisk run \
  --why "Verify the selected implementation before review" \
  --expect "Focused tests pass" \
  --check tests \
  --evidence verification \
  -- uv run pytest tests/test_feature.py -q

wisk check
```

Expected effect:

```text
LoopRun
├── RunExecution(argv=pytest..., exit_code=0)
├── RunEvidence(kind=verification, reference=RunExecution)
└── RunCheck(kind=tests, status=pass, evidence=RunEvidence)
```

### TDD RED → GREEN

RED:

```bash
wisk run \
  --why "Demonstrate the missing behavior before implementation" \
  --expect "Exactly one focused regression test fails" \
  --evidence red-test \
  -- uv run pytest tests/test_null_parity.py -q
```

GREEN:

```bash
wisk run \
  --why "Verify the implementation against the same behavior contract" \
  --expect "The focused regression test passes" \
  --evidence green-test \
  --check tests \
  -- uv run pytest tests/test_null_parity.py -q
```

The failing RED command is valuable persisted execution evidence but does not satisfy `check:tests`. The GREEN command can.

### Skill-guided investigation

```bash
wisk run \
  --using skill-audit-duplicated-domain-logic@1.2.0 \
  --why "Apply the learned duplicate-logic search procedure" \
  --expect "Find all local classifier implementations, including ops scripts" \
  --evidence investigation \
  -- rg "classify|normalize" src scripts tools
```

The later Wiki Maintainer can query which Work runs actually exercised that skill version and inspect the execution/evidence graph.

### External execution remains valid

```text
IDE or MCP tool performs the work
→ wisk record evidence ...
→ wisk record check ...
→ wisk check
```

No synthetic `RunExecution` is created because Wisk did not observe that process.

## Non-goals

This RFC does not make Wisk:

- a mandatory shell for every agent action;
- a replacement for CI, IDEs, MCPs, GitHub Actions, browsers, or provider tools;
- a chain-of-thought recorder;
- a universal log archive;
- an inference engine that turns every exit-zero command into semantic evidence;
- a second scheduler beside SessionType/RunSpec/LoopRun;
- a workflow DSL that forces every repository to use the same artifacts.

The active Wisk contracts continue to decide which typed artifacts are required.

## 0.4 RC implementation requirements

The implementation stacked on RFC 0007 should prove at least:

1. `wisk run -- <argv>` executes direct argv with no implicit shell;
2. the canonical `start` operation is reused to resolve/resume the LoopRun;
3. every observed command creates a valid child-owned `RunExecution`;
4. `started_at`, `finished_at`, exit code, cwd, argv, output digest/retention state, and Git before/after are persisted when available;
5. `--why` and `--expect` remain optional declarative metadata and do not satisfy unrelated RunSpec requirements;
6. `--evidence <kind>` creates execution-backed `RunEvidence` only because the caller explicitly requested the relationship;
7. `--check <kind>` maps exit status deterministically into a `RunCheck` and does not turn an expected RED test into a passing check;
8. `--observe` and `--using` can preserve command-bound observation/skill provenance without a second typed-write command;
9. `wisk record` becomes the documented manual write namespace, with RC aliases for the old `wisk run <record-type>` surface where compatibility is useful;
10. `check` before/after yields `next_before` / `next_after` from the same authoritative runtime logic;
11. non-zero child exit codes are recorded faithfully and propagated appropriately;
12. a post-execution Wisk failure reports that the command may already have had effects;
13. output capture is bounded/policy-driven and does not persist the full environment by default;
14. an external execution can still satisfy the same final contract using truthful typed records plus `check`;
15. MCP only claims command execution when the server actually has that capability.

## Dogfood criterion

The CausaGanha golden corpus from RFC 0007 should exercise this path before stable `0.4.0`.

At least one real Work run should use `wisk run` to produce a `RunExecution` plus meaningful typed projections, and a later Wiki/Skill run should be able to consume that trace without relying on provider conversation history.

The ideal demonstration is a real TDD or investigation chain in which:

```text
wisk run captures a prediction + execution
→ evidence/check/observation is linked to that execution
→ the Work run closes
→ a later Wiki Maintainer can inspect the persisted trace
→ later procedural learning can distinguish what the Worker actually did from what it merely concluded afterward
```

That is the purpose of the golden path: not command wrapping for its own sake, but making real agent work durable enough to learn from.