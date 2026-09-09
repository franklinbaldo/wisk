from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from wisk import Wisk

ROOT = Path(__file__).parent.parent


def _temp_bundle(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    shutil.copytree(ROOT / "specs", tmp_path / "specs")
    return tmp_path / "knowledge"


def _write_concept(path: Path, frontmatter: dict[str, object]) -> None:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(["---", "", "# Test concept", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _closure_run(knowledge_path: Path, task: str) -> tuple[Wisk, str]:
    _write_concept(
        knowledge_path / "skills" / "run-specs" / "closure-test.md",
        {
            "type": "RunSpec",
            "id": "run-specs/closure-test",
            "title": "Closure test",
            "version": "1.0.0",
            "status": "experimental",
            "required_reading_kinds": [],
            "required_goal_kinds": [],
            "required_evidence_kinds": [],
            "required_check_kinds": [],
            "allowed_result_states": ["success", "partial"],
        },
    )
    ws = Wisk.open(knowledge_path)
    started = ws.start_run(task, "run-specs/closure-test")
    return ws, started["run_id"]


def test_active_goal_blocks_outcome_until_achieved(tmp_path: Path) -> None:
    knowledge_path = _temp_bundle(tmp_path)
    ws, run_id = _closure_run(knowledge_path, "finish one goal")
    goal = ws.record_run_goal(
        run=run_id,
        component_id="finish",
        kind="task-advance",
        goal="Finish the useful work owned by this run.",
        rationale="The run should close only after its intent has a destination.",
        success_signal="The work is complete and verified.",
    )
    goal_id = goal["id"]

    with pytest.raises(ValueError, match="goal-state"):
        Wisk.open(knowledge_path).record_run_outcome(
            run=run_id,
            component_id="done",
            result_state="success",
            work_status="complete",
            summary="Attempted to close while the goal was still active.",
            next_move="None.",
        )

    updated = Wisk.open(knowledge_path).update_run_goal_status(
        run=run_id,
        goal=goal_id,
        status="achieved",
    )
    assert updated["status"] == "achieved"
    assert not any(item["kind"] == "goal-state" for item in updated["check"]["unsatisfied"])

    outcome = Wisk.open(knowledge_path).record_run_outcome(
        run=run_id,
        component_id="done",
        result_state="success",
        work_status="complete",
        summary="The goal is achieved and the run can close.",
        next_move="A future run may choose a new goal.",
    )
    assert outcome["run_status"] == "closed"
    assert outcome["check"]["conformant"] is True


def test_carried_goal_requires_explicit_handoff_link(tmp_path: Path) -> None:
    knowledge_path = _temp_bundle(tmp_path)
    ws, run_id = _closure_run(knowledge_path, "carry one goal")
    goal = ws.record_run_goal(
        run=run_id,
        component_id="carry",
        kind="task-advance",
        goal="Continue material work in a later run.",
        rationale="The current run cannot finish the whole task.",
        success_signal="A later run has an explicit continuation point.",
    )
    goal_id = goal["id"]
    Wisk.open(knowledge_path).update_run_goal_status(
        run=run_id,
        goal=goal_id,
        status="carried_forward",
    )

    before = Wisk.open(knowledge_path).check_run(run_id)
    assert f"handoff:{goal_id}" in {item["requirement"] for item in before["unsatisfied"]}

    with pytest.raises(ValueError, match="Handoff"):
        Wisk.open(knowledge_path).record_run_outcome(
            run=run_id,
            component_id="partial",
            result_state="partial",
            work_status="partial",
            summary="The unfinished goal has no destination yet.",
            next_move="Create the handoff.",
        )

    handoff = Wisk.open(knowledge_path).create_handoff(
        handoff_id="carry-goal",
        title="Continue the carried goal",
        created_by_run=run_id,
        state="The current run stopped with one material goal remaining.",
        next_action="Resume the carried goal in the next appropriate run.",
        goals=[goal_id],
        references=["#continuation"],
    )
    assert handoff["status"] == "active"

    closed = Wisk.open(knowledge_path).record_run_outcome(
        run=run_id,
        component_id="partial",
        result_state="partial",
        work_status="partial",
        summary="The remaining intent is explicitly handed off.",
        next_move="Resume the linked Handoff.",
    )
    assert closed["check"]["conformant"] is True

    _, later_run = _closure_run(knowledge_path, "resume carried goal")
    Wisk.open(knowledge_path).continue_handoff(
        handoff=handoff["id"],
        continued_by_run=later_run,
        resolution="The later run resumed the carried work.",
    )
    historical = Wisk.open(knowledge_path).check_run(run_id)
    assert historical["conformant"] is True
    assert historical["handoffs_created"] == 1
    assert historical["active_handoffs_created"] == 0


def test_handoff_rejects_goal_from_another_run(tmp_path: Path) -> None:
    knowledge_path = _temp_bundle(tmp_path)
    ws, first_run = _closure_run(knowledge_path, "first run")
    first_goal = ws.record_run_goal(
        run=first_run,
        component_id="first",
        kind="task-advance",
        goal="First run goal.",
        rationale="Belongs to the first run.",
        success_signal="First run advances.",
    )
    _, second_run = _closure_run(knowledge_path, "second run")

    with pytest.raises(ValueError, match="another run"):
        Wisk.open(knowledge_path).create_handoff(
            handoff_id="wrong-run",
            title="Wrong run",
            created_by_run=second_run,
            state="This should not be writable.",
            next_action="Reject it.",
            goals=[first_goal["id"]],
        )
