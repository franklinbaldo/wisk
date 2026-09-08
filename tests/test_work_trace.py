from __future__ import annotations

from pathlib import Path

import pytest

from wisk import Wisk
from wisk.bootstrap import init_repository


def _initialized(tmp_path: Path) -> tuple[Path, Wisk]:
    result = init_repository(tmp_path)
    assert result["status"] == "initialized"
    knowledge = tmp_path / ".wisk/knowledge"
    return knowledge, Wisk.open(knowledge)


def test_worker_context_excludes_wiki_and_synthesis_context_sees_closed_work(tmp_path: Path) -> None:
    knowledge, ws = _initialized(tmp_path)

    worker = ws.context("Adopt Wisk in this repository", "session-types/standard-work")
    assert worker["session_type"] == "session-types/standard-work"
    assert worker["wiki"] == []
    assert worker["recent_experiences"] == []
    assert worker["recent_work_runs"] == []
    assert worker["skill_proposals"] == []
    assert any(item["id"] == "skill-adopt-wisk-consumer" for item in worker["skills"])

    started = Wisk.open(knowledge).start(
        "Adopt Wisk in this repository",
        session_type="session-types/standard-work",
    )
    run = str(started["run"])
    assert started["state"] == "next"
    assert started["session_type"] == "session-types/standard-work"

    runtime = Wisk.open(knowledge)
    runtime.record_run_reading(
        run=run,
        component_id="active-handoffs",
        kind="active-handoffs",
        subject="Active handoffs",
        reference="wisk:handoffs",
        finding="No prior operational responsibility blocks this Work run.",
    )
    runtime.record_run_reading(
        run=run,
        component_id="active-skills",
        kind="active-skills",
        subject="Applicable skills",
        reference="skill-adopt-wisk-consumer",
        finding="The active adoption skill applies to this task.",
    )
    goal = runtime.record_run_goal(
        run=run,
        component_id="task-advance",
        kind="task-advance",
        goal="Exercise one complete RFC 0007 Work trace.",
        rationale="The RC must preserve raw execution metadata for later synthesis.",
        success_signal="The closed trace can be reconstructed without parent backlinks.",
    )
    runtime.record_run_skill_use(
        run=run,
        component_id="adoption-skill",
        skill="skill-adopt-wisk-consumer",
        skill_version="1.1.0",
        skill_status="active",
        notes="Used as the operating procedure for this Work run.",
    )
    observation = runtime.record_run_observation(
        run=run,
        component_id="hot-context",
        kind="friction",
        summary="A later Wiki session could not reconstruct local execution friction unless Work persisted it while context was hot.",
        impact="high",
    )
    runtime.record_run_evidence(
        run=run,
        component_id="execution",
        kind="execution",
        reference="tests/test_work_trace.py",
        summary="The Work runtime persisted child-owned Raw Layer records.",
        goal=str(goal["id"]),
    )
    runtime.record_run_check(
        run=run,
        component_id="verification",
        kind="verification",
        procedure="Reconstruct the trace from child run links.",
        result="Raw trace contains the recorded skill use and observation.",
        status="pass",
    )
    runtime.update_run_goal_status(run=run, goal=str(goal["id"]), status="achieved")
    outcome = runtime.record_run_outcome(
        run=run,
        component_id="complete",
        result_state="success",
        work_status="complete",
        summary="The Work trace is complete and queryable.",
        next_move="A later Wiki Maintainer may compare this episode with other Work traces.",
    )

    assert outcome["finished_at"]
    assert outcome["duration_seconds"] >= 0

    trace = Wisk.open(knowledge).run_trace(run)
    assert trace["run"]["started_at"]
    assert trace["run"]["finished_at"]
    assert trace["run"]["status"] == "closed"
    assert trace["duration_seconds"] is not None
    assert [item["skill_version"] for item in trace["skill_uses"]] == ["1.1.0"]
    assert [item["id"] for item in trace["observations"]] == [observation["id"]]
    assert "readings" not in trace["run"]
    assert "evidence" not in trace["run"]
    assert "checks" not in trace["run"]

    wiki = Wisk.open(knowledge).context("Synthesize adoption traces", "session-types/standard-wiki")
    assert wiki["active_handoffs"] == []
    assert any(item["id"] == run for item in wiki["recent_work_runs"])
    assert wiki["skills"] == []
    assert wiki["skill_proposals"] == []

    skill = Wisk.open(knowledge).context("Evolve adoption procedure", "session-types/standard-skill")
    assert any(item["id"] == run for item in skill["recent_work_runs"])
    assert any(item["id"] == "skill-adopt-wisk-consumer" for item in skill["skills"])
    assert "skill_proposals" in skill


def test_skill_use_rejects_version_or_status_that_does_not_match_skill(tmp_path: Path) -> None:
    knowledge, ws = _initialized(tmp_path)
    started = ws.start_run(
        "Exercise skill provenance",
        run_spec_id="run-specs/work",
        session_type_id="session-types/standard-work",
    )
    run = str(started["run_id"])

    with pytest.raises(ValueError, match="skill_version does not match"):
        Wisk.open(knowledge).record_run_skill_use(
            run=run,
            component_id="wrong-version",
            skill="skill-adopt-wisk-consumer",
            skill_version="9.9.9",
            skill_status="active",
        )

    with pytest.raises(ValueError, match="skill_status does not match"):
        Wisk.open(knowledge).record_run_skill_use(
            run=run,
            component_id="wrong-status",
            skill="skill-adopt-wisk-consumer",
            skill_version="1.1.0",
            skill_status="experimental",
        )


def test_run_observation_is_execution_fact_not_required_synthesis(tmp_path: Path) -> None:
    knowledge, ws = _initialized(tmp_path)
    started = ws.start_run(
        "Record local execution texture",
        run_spec_id="run-specs/work",
        session_type_id="session-types/standard-work",
    )
    run = str(started["run_id"])

    recorded = Wisk.open(knowledge).record_run_observation(
        run=run,
        component_id="near-miss",
        kind="near_miss",
        summary="A destructive write was detected before commit by inspecting the diff.",
        impact="high",
    )

    assert recorded["id"].startswith("run-observations/")
    check = Wisk.open(knowledge).check_run(run)
    assert check["counts"]["observations"] == 1
    assert "observation" not in {item["kind"] for item in check["unsatisfied"]}
