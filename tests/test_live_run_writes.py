from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from wisk import Wisk

ROOT = Path(__file__).parent.parent


def _copy_bundle(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    shutil.copytree(ROOT / "specs", tmp_path / "specs")
    return tmp_path / "knowledge"


def test_typed_writes_drive_run_from_scaffold_to_closed(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge)
    started = ws.start_run(
        "exercise typed live-run writes",
        "run-specs/wisk-development",
    )
    run_id = started["run_id"]

    for kind in [
        "repository-guide",
        "open-issues",
        "open-prs",
        "okf-knowledge",
        "recent-runs",
        "active-handoffs",
    ]:
        result = ws.record_run_reading(
            run=run_id,
            component_id=kind,
            kind=kind,
            subject=kind,
            reference=f"ref:{kind}",
            finding=f"finding for {kind}",
        )
    assert result["run_status"] == "in_progress"

    goal = ws.record_run_goal(
        run=run_id,
        component_id="project-advance",
        kind="project-advance",
        goal="prove typed run writes",
        rationale="remove direct Markdown mutation from the live loop",
        success_signal="the pinned RunSpec becomes conformant through runtime calls",
        status="achieved",
    )
    ws.record_run_decision(
        run=run_id,
        component_id="typed-service-layer",
        question="How should live run state be persisted?",
        decision="Use typed runtime methods with validated atomic writes.",
        rationale="Agents should not need to know the bundle storage topology.",
        goal=goal["id"],
        alternatives=["hand-write Markdown"],
    )
    ws.record_run_evidence(
        run=run_id,
        component_id="change",
        kind="change",
        reference="src/wisk/live_run.py",
        summary="typed component writer persists and attaches run state",
        goal=goal["id"],
    )
    verification = ws.record_run_evidence(
        run=run_id,
        component_id="verification",
        kind="verification",
        reference="tests/test_live_run_writes.py",
        summary="integration test exercises the complete contract",
        goal=goal["id"],
    )
    ws.record_run_check(
        run=run_id,
        component_id="okf",
        kind="okf",
        procedure="validate the normative OKF bundle",
        result="bundle conformant",
        status="pass",
        evidence=verification["id"],
        goal=goal["id"],
    )
    ws.record_run_check(
        run=run_id,
        component_id="tests",
        kind="tests",
        procedure="run the test suite",
        result="tests pass",
        status="pass",
        evidence=verification["id"],
        goal=goal["id"],
    )
    outcome = ws.record_run_outcome(
        run=run_id,
        component_id="complete",
        result_state="green",
        work_status="complete",
        summary="the run was completed using only typed runtime writes",
        next_move="expose these writes through CLI and MCP",
    )

    assert outcome["run_status"] == "closed"
    assert outcome["check"]["conformant"] is True
    assert outcome["check"]["next_action"]["kind"] == "complete"

    run = Wisk.open(knowledge)._find_record("LoopRun", run_id)
    frontmatter = run["frontmatter"]
    assert frontmatter["status"] == "closed"
    assert "readings" not in frontmatter
    assert "outcome" not in frontmatter

    components = Wisk.open(knowledge)._run_components("RunOutcome", run_id)
    assert [item["frontmatter"]["id"] for item in components] == [outcome["id"]]

    with pytest.raises(ValueError, match="already closed"):
        ws.record_run_evidence(
            run=run_id,
            component_id="late",
            kind="verification",
            reference="late",
            summary="must not be accepted",
        )


def test_component_collision_is_explicit_and_does_not_duplicate_link(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge)
    run_id = ws.start_run("collision proof", "run-specs/wisk-development")["run_id"]

    first = ws.record_run_reading(
        run=run_id,
        component_id="repository-guide",
        kind="repository-guide",
        subject="CLAUDE.md",
        reference="CLAUDE.md",
        finding="repository instructions",
    )
    with pytest.raises(FileExistsError):
        ws.record_run_reading(
            run=run_id,
            component_id="repository-guide",
            kind="repository-guide",
            subject="CLAUDE.md",
            reference="CLAUDE.md",
            finding="duplicate",
        )

    readings = Wisk.open(knowledge)._run_components("RunReading", run_id)
    assert [item["frontmatter"]["id"] for item in readings] == [first["id"]]


def test_outcome_refuses_unmet_run_prerequisites(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge)
    run_id = ws.start_run("premature outcome", "run-specs/wisk-development")["run_id"]

    with pytest.raises(ValueError, match="unmet prerequisites"):
        ws.record_run_outcome(
            run=run_id,
            component_id="premature",
            result_state="blocked",
            work_status="complete",
            summary="must not close an unsatisfied run",
            next_move="satisfy the contract first",
        )

    run = Wisk.open(knowledge)._find_record("LoopRun", run_id)
    assert run["frontmatter"]["status"] == "scaffold"
    assert not run["frontmatter"].get("outcome")


def test_failing_check_keeps_the_run_open_until_a_later_check_passes(tmp_path: Path) -> None:
    """A recorded check of the required kind is not verification: it must stand at pass."""
    knowledge = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge)
    run_id = ws.start_run("standing check proof", "run-specs/wisk-development")["run_id"]

    failing = ws.record_run_check(
        run=run_id,
        component_id="tests-red",
        kind="tests",
        procedure="run the test suite",
        result="two tests fail",
        status="fail",
        observed_at="2026-09-08T10:00:00Z",
    )
    outstanding = {item["requirement"] for item in failing["check"]["unsatisfied"]}
    assert "check:tests" in outstanding

    passing = ws.record_run_check(
        run=run_id,
        component_id="tests-green",
        kind="tests",
        procedure="run the test suite",
        result="tests pass",
        status="pass",
        observed_at="2026-09-08T11:00:00Z",
    )
    outstanding = {item["requirement"] for item in passing["check"]["unsatisfied"]}
    assert "check:tests" not in outstanding


def _standing(*checks: tuple[str, str | None]) -> str:
    from wisk.runtime import _standing_check

    records = []
    for status, observed_at in checks:
        frontmatter: dict[str, object] = {"kind": "tests", "status": status}
        if observed_at is not None:
            frontmatter["observed_at"] = observed_at
        records.append({"frontmatter": frontmatter})
    standing = _standing_check(records, "tests")
    assert standing is not None
    return str(standing["frontmatter"]["status"])


def test_a_later_check_supersedes_an_earlier_one_in_both_directions() -> None:
    assert _standing(("fail", "2026-09-01T10:00:00Z"), ("pass", "2026-09-01T11:00:00Z")) == "pass"
    assert _standing(("pass", "2026-09-01T10:00:00Z"), ("fail", "2026-09-01T11:00:00Z")) == "fail"
    assert (
        _standing(("pass", "2026-09-01T10:00:00Z"), ("inconclusive", "2026-09-01T11:00:00Z"))
        == "inconclusive"
    )


def test_standing_check_orders_by_instant_not_by_timestamp_text() -> None:
    """`12:00-03:00` is later than `14:00Z`, though it sorts earlier as a string."""
    assert (
        _standing(("pass", "2026-09-01T14:00:00Z"), ("fail", "2026-09-01T12:00:00-03:00")) == "fail"
    )


def test_an_unorderable_check_never_grants_closure_on_a_guess() -> None:
    """A missing or unparseable `observed_at` must not let a stale pass mask a failure."""
    assert _standing(("pass", "2026-09-01T10:00:00Z"), ("fail", None)) == "fail"
    assert _standing(("pass", "2026-09-01T10:00:00Z"), ("fail", "not-a-date")) == "fail"
    assert _standing(("pass", "2026-09-01T10:00:00Z"), ("fail", "2026-09-01T10:00:00Z")) == "fail"
    assert _standing(("pass", None)) == "pass"


def test_a_recorded_check_always_carries_an_objective_instant(tmp_path: Path) -> None:
    """Without this, a later failing check would be unorderable against an earlier pass."""
    knowledge = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge)
    run_id = ws.start_run("timestamp defaulting", "run-specs/wisk-development")["run_id"]

    recorded = ws.record_run_check(
        run=run_id,
        component_id="untimestamped",
        kind="tests",
        procedure="uv run pytest",
        result="green",
        status="pass",
    )
    written = Path(recorded["path"]).read_text(encoding="utf-8")

    assert "observed_at:" in written
