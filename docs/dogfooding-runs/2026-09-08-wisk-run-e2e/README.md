# Dogfooding run — `wisk run` end to end, 2026-09-08

An end-to-end consumer session driven entirely through the `0.4.0rc1` CLI built from
`rfc/wisk-run-golden-path` (PR #71, stacked on PR #70). The session's own task was to
reproduce and diagnose the single CI failure attributable to #71.

Everything under `trace/` is the raw bundle Wisk itself wrote — `wisk trace` output plus the
`LoopRun` and its typed children, copied verbatim from the consumer repository. Absolute paths
are preserved because they are part of the observed fact.

## How the session was run

```sh
uv venv .venv
uv pip install -e <clone of rfc/wisk-run-golden-path>
wisk init
wisk start "Reproduzir e diagnosticar a falha de exit_code no run_trace da RFC 0003"
wisk record reading  ...    # active-handoffs, active-skills
wisk record goal     ...
wisk run --run <run> --cwd <wisk clone> \
    --why "Reproduzir localmente a falha unica atribuivel a #71" \
    --expect "..." --evidence red-test --using skill-adopt-wisk-consumer@1.1.0 \
    -- <python> -m pytest tests/test_execution.py -q
wisk record evidence / check / observation / goal-status
wisk handoff create ...
wisk trace <run>
```

Final state: 3 `RunExecution`, 3 `RunEvidence`, 1 `RunCheck` (`fail`), 1 resolved `RunGoal`,
8 `RunObservation`, 1 `Handoff`, **0 `RunOutcome`** — see friction 8 for why the run could not
be closed.

## What the golden path did well

`wisk run -- <argv>` behaved as RFC 0003 specifies: real subprocess with `shell=False`, the `--`
boundary held with an absolute interpreter path and pytest flags after it, `--why` and `--expect`
were recorded as pre-execution declarations without becoming reasoning, `--using` validated the
skill version before the command ran, and `--evidence red-test` recorded a failing run as evidence
without fabricating a green check. The missing-plugin case (exit 4, no `pytest-cov`) was recorded
as an ordinary non-zero exit with `launch_error: null`, which is the honest classification.

## Finding 1 — CI attribution for #70 + #71

Run `34274636808` (combined tree) and run `34274136932` (#70 alone) fail with the same 9 tests,
except one:

- 8 failures already fail on #70 alone — inheritance ordering (`session-types/work` vs
  `base`/`experience`), removed wording (`truthful raw episodic evidence`), the
  `Recorded legacy Experience` message, `selection_reason`. These are tests not yet updated for
  the pivot, not regressions from #71.
- 1 failure is #71's own:
  `tests/test_execution.py::test_execute_command_records_raw_fact_without_inventing_semantics`,
  `assert '0' == 0`.

## Finding 2 — the failing assertion is a symptom of typed round-trip loss

Inspecting the files this session wrote:

```text
exit_code: "1"             # was int 1
exit_code                  # absent entirely when the value is 0
git_dirty_before: "false"  # a truthy string
stdout_bytes: "2642"       # string
```

`_record_raw_component` writes correctly typed JSON (`_render_markdown` uses `json.dumps`). The
damage happens afterwards: `src/wisk/execution.py:336 _update_execution_next` re-reads the record
through `_find_record` — whose frontmatter has already passed through the OKF loader, which
stringifies scalars and drops falsy values — and rewrites the file from that degraded dict. Every
`RunExecution` is written correctly and immediately corrupted by the `next_after` update.

The `Handoff` written in the same session keeps `repository_dirty: true` as a real boolean, because
nothing rewrites it. That isolates the fault to the rewrite path.

Consequences beyond the failing test:

- a consumer reading `git_dirty_before` from a trace gets `"false"`, which is truthy — the trace
  misreports a clean tree;
- `exit_code == 0`, the most common case, is not persisted at all.

Suggested fix: rewrite from the original field values (or type the loader's deserialization), with a
round-trip test covering `exit_code` 0 and 1 and `git_dirty` false.

Separately, on Windows the same test fails earlier, at `result["stdout"] == "hello from worker\n"` —
the captured bytes carry `\r\n` and `execute_command` decodes without normalizing newlines.

## Finding 3 — eight recorded frictions

Each was recorded as a `RunObservation` of kind `friction` during the session; the raw records are
in `trace/`. For each: what the agent experience should be, and what the current design gets right.

### 1. Two mandatory `RunReading`s before any work

`wisk start` requires `active-handoffs` and `active-skills` in a freshly initialized repository,
where both can only say "there is nothing".

**Should be:** Wisk just generated the bundle and knows both sets are empty. Satisfy the requirement
with a derived reading (`observed: none, source: bundle-scan`) and demand a written reading only
when there is something to read.

**Value today:** the obligation stops an agent from ignoring work left by another session, which is
the chronic failure of memoryless agents. The mistake is applying the ritual to a provably empty
set, not the ritual itself.

### 2. `--component-id` hand-invented on every record

`reading-active-handoffs`, `goal-diagnose-exit-code`, `obs-...` — slugs carrying no information
beyond `kind` + timestamp, and the most likely cause of `FileExistsError` in repeated sessions.

**Should be:** optional, defaulting to `kind` + timestamp; explicit only when the agent wants a
stable id to reference later.

**Value today:** deterministic ids make recording idempotent — re-running the same command does not
duplicate the fact. That is worth keeping. It just does not need to be typed.

### 3. `wisk run --help` documents no parameter

No help string on any flag, and cyclopts renders confusing pairs like `--evidence --empty-evidence`.
Reading `src/wisk/execution.py` was required to learn that `--evidence` and `--check` take a free
kind.

**Should be:** help as executable contract — one line per flag and a canonical example in the footer
(`wisk run --check verification -- pytest -q`). For a tool whose audience is an agent, the `--help`
output *is* the API.

**Value today:** none. This is pure debt.

### 4. JSON envelope on stderr, child stdout on Wisk's stdout

Confirmed with a silent command: stdout 0 bytes, the whole envelope on stderr. `wisk run ... > out.json`
captures the command's output, not the envelope.

**Should be:** Wisk's stdout is the envelope, always and only; the child's output goes to stderr, to
`--stdout-file`, or stays as a digest.

**Value today:** streaming the child's output live is genuinely useful — the agent watches pytest
fail as it happens rather than afterwards. Both are achievable by separating the channels the other
way round.

### 5. `--evidence red-test` leaves `evidence:execution` unsatisfied

A real command ran, and the contract still asks for execution evidence.

**Should be:** a real `RunExecution` should satisfy `evidence:execution` by itself — it *is* the
evidence of the execution; `red-test` is an additional semantic reading over it, not a substitute.

**Value today:** the RED-versus-green distinction is the best idea in RFC 0003 and does need to be
explicit. Only the double record over the same fact is wrong.

### 6. `record reading` requires six fields to record an empty fact

`subject` and `reference` become filler text when there is nothing to reference.

**Should be:** required-ness proportional to content — `finding` always; `subject`/`reference`
required only when something is actually referenced.

**Value today:** required fields are what stop an agent from recording "ok, read it" without saying
what it read. The cost is only misplaced in the empty case.

### 7. Enum values discoverable only by traceback

`--work-status` and `--result-state` appear in help as bare `[required]`. `complete|partial` was
discovered by triggering a `ValueError` that the CLI let escape as a full Python traceback; likewise
"Partial RunOutcome requires a Handoff".

**Should be:** enums in the help, and runtime `ValueError` translated into a handled CLI error
carrying the allowed values and the suggested next command. A traceback is an implementation leak.

**Value today:** the messages themselves are good — they say exactly what is missing. They are only
wrapped wrong and hidden until the agent errs.

### 8. An honest session that finds a bug cannot close

A `RunCheck` of kind `verification` with status `fail` does not satisfy `check:verification`:
`src/wisk/runtime.py:79` requires `pass`, and the message reads *"Record a later check of the same
kind that passes."* Escaping through `work_status=partial` plus a `Handoff` is blocked by the same
gate on `RunOutcome`. This run remains open with `unsatisfied: ['check:verification', 'outcome']`
despite a resolved goal, evidence, a root cause and a created handoff.

**Should be:** `fail` should *satisfy* the verification requirement — what the contract needs to
guarantee is that verification *happened*, not that it succeeded. Whether a run with a red check may
close is decided by `result_state` (`diagnosed`, `blocked`) together with a handoff.

**Value today:** the intent is legitimate — stop an agent from declaring victory without verifying.
But the implementation conflates *verified* with *passed*, and in a tool whose normative text speaks
of "truthful raw episodic evidence" that incentive points exactly the wrong way: the only available
route to a closed run is to record a green check about some other proposition.
