# RunExecution persistence verification — 2026-09-12

This is a follow-up to the September 8 session, not a replacement trace. All files
under `trace/` remain unchanged. Their corrupted scalars and open run state are
historical evidence; this change neither reconstructs lost values nor closes that run.

## Reconstructed stack

- #70 merged into `main` as `7f9e0618708efc4d0be30b7ba821760432b06416`.
- #71 previously ended at `89fee6aed8a45b8475c98657330c4ebac70c8362` and still targeted
  #70's old branch. Its two commits were replayed onto main.
- #72 previously ended at `f62aa683365bd45cfddd20d3bd439000afa6dce4`, based on
  `e4b172336bf44e87e3d07f95949fbf83a058b051`. Its documentation commit was replayed
  onto the corrected #71, preserving the original evidence.

## What was still broken

The original session identified whole-record rewriting from a lossy frontmatter
projection. The later #71 already routed the public `Wisk` class through
`OKFExecutionWisk`, whose update delegated to `okf-parser.apply_bundle` with the
declared schema. That avoided the old rewrite but had not made execution usable.

On the rebased tree with the locked dependencies (`okf-parser==0.45.9`), the original
execution test file produced **5 failures and 4 passes**. The failure was:

```text
Binder Error: Cant update column "next_after" because it is a generated column!
```

This happens after the child command runs and is correctly surfaced as
`ExecutionPersistenceError(effect_may_have_occurred=True)`.

## Smallest correction

The adapter patches only the optional `next_after` string through the parser's
untyped transactional writer. Schema-backed typed relations remain the read path.
No Wisk YAML parser or whole-record serializer is introduced. The parser still owns
candidate validation, conflict checks and writing.

The writer adds the column only when no RunExecution has authored it. Version
0.45.9 also rejects a no-op `ADD COLUMN IF NOT EXISTS` as affecting no table, so an
unconditional ALTER would fix the first write but break repeated updates. Values
and paths use the existing SQL literal quoting helper. An update failure propagates
without erasing the already observed execution record.

The adapter also declares its own `open()` returning `Self`, resolving the
incompatible inherited factory return types caught by `ty`.

## Regression coverage

The tests execute real child processes and inspect both stored YAML and a newly
opened public trace:

- integer exit codes 0 and 3;
- integer zero stdout/stderr byte counts;
- a real clean Git tree (`false`) and a command that makes it dirty (`true`);
- argv preservation;
- repeated `next_after` replacement and removal, preserving every other field;
- rejected persistence after a command effect, retaining the original record;
- CRLF display normalization while preserving exact raw byte counts and SHA-256
  digests for both stdout and stderr.

The original stdout byte-count assertion now uses the platform line ending: a
normalized display string does not change what bytes the subprocess emitted.

## Scope

The eight UX observations in the original report remain proposals to evaluate.
This correction does not make a failing RunCheck satisfy a passing-check requirement,
change stdout/stderr policy, or alter the stable 0.4 learning-loop promotion gates.
Historical CI attribution in the September 8 report describes those historical
commits, not current main.

## Reproduction and observed results

The runtime tree tested locally is `84288bd3cf85a88b39fc18fd5b53301ca075e87d`,
published in #71 as commit `3f9483be15b71401ef3b645ad20c685f1ef401d8`.
The published Git tree SHA was checked against the local tree.

```sh
uv sync --locked
uv run pytest tests/test_execution.py -q --no-cov
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run bandit -r src/ -c pyproject.toml
uv run vulture src/ --min-confidence 80
uv run scripts/check_pep723.py
uv run scripts/check_version.py
uv run okf-parser check knowledge/ --require-spec '../specs/{slug}.md' --normative-spec
uv build --wheel
```

- Focused execution suite: 12 passed before the final write-conflict test was added.
- GitHub normal-dependency full suite: **111 passed**, **80.36% coverage**
  (job `103594123699`, 486.56 seconds). This includes the write-conflict regression.
- GitHub lowest-direct-dependency full suite: **111 passed**, **80.36% coverage**
  (job `103594123616`, 600.56 seconds); normative conformance also passed.
- Local locked-dependency full suite: **111 passed**, **80.36% coverage**
  (Python 3.12.14, 916.27 seconds).
- Ruff, format, ty, Bandit, Vulture, PEP 723 and version checks: passed.
- Normative bundle: 49 concepts, zero diagnostics.
- Wheel build: passed.
- Separate installed-consumer smoke: passed, using a uv project with the wheel as
  a dependency. `wisk init`, two `wisk start` calls and `wisk run -- python -c
  'print("wheel-ok")'` confirmed resumability, the child's output, integer exit
  code 0 and zero stderr bytes in a reopened trace. Wisk was imported from the
  consumer's site-packages, not this source checkout.

GitHub's normal and lowest-direct-dependency suites run in
[CI 34708978637](https://github.com/franklinbaldo/wisk/actions/runs/34708978637).
The workflow targets PRs based on main, so #72 has no separate runtime CI while
stacked; its changes relative to #71 are documentation and historical evidence only.
