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
