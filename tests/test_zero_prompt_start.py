from __future__ import annotations

import json
from pathlib import Path

from wisk import Wisk
from wisk.bootstrap import init_repository


def _initialized_bundle(tmp_path: Path) -> Path:
    result = init_repository(tmp_path)
    assert result["status"] == "initialized"
    return tmp_path / ".wisk" / "knowledge"


def _write_concept(path: Path, frontmatter: dict[str, object]) -> None:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(["---", "", "# Test concept", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def test_zero_prompt_start_returns_next_and_resumes_same_live_run(tmp_path: Path) -> None:
    knowledge = _initialized_bundle(tmp_path)

    first = Wisk.open(knowledge).start()
    assert first["state"] == "next"
    assert first["run"]
    assert first["resumed"] is False
    assert first["selection_reason"]
    assert first["next"]

    second = Wisk.open(knowledge).start()
    assert second["state"] == "next"
    assert second["run"] == first["run"]
    assert second["resumed"] is True
    assert second["selection_reason"] == "active-run-resume"
    assert second["next"] == first["next"]


def test_explicit_session_type_override_starts_without_cadence_reason(tmp_path: Path) -> None:
    knowledge = _initialized_bundle(tmp_path)

    result = Wisk.open(knowledge).start(session_type="session-types/experience")

    assert result["state"] == "next"
    assert result["session_type"] == "session-types/experience"
    assert result["selection_reason"] == "explicit-override"


def test_resumed_handoff_requires_environment_then_disposition(tmp_path: Path) -> None:
    knowledge = _initialized_bundle(tmp_path)
    handoff_path = knowledge / "local" / "handoffs" / "resume-me.md"
    _write_concept(
        handoff_path,
        {
            "type": "Handoff",
            "id": "handoffs/resume-me",
            "title": "Resume carefully",
            "created_at": "2026-09-07T00:00:00Z",
            "status": "active",
            "created_by_run": "runs/historical-source",
            "target_session_type": "session-types/standard-experience",
            "state": "A previous session proposed continuing this work.",
            "next_action": "Continue only after revalidating repository assumptions.",
            "references": [],
            "goals": [],
            "repository_head": "abc123",
            "repository_branch": "main",
            "repository_dirty": False,
            "repository_diff_digest": "",
        },
    )

    started = Wisk.open(knowledge).start()
    run = str(started["run"])
    assert started["selection_reason"] == "handoff-continuation"
    assert started["next"]["kind"] == "handoff-environment"

    after_environment = Wisk.open(knowledge).record_run_check(
        run=run,
        component_id="environment-revalidated",
        kind="handoff-environment",
        procedure="Compare current repository/environment with the persisted handoff baseline.",
        result="unchanged baseline; prior assumptions remain reviewable",
        status="pass",
        evidence="repository baseline comparison",
    )
    assert after_environment["state"] == "next"
    assert after_environment["next"]["kind"] == "handoff-disposition"

    after_disposition = Wisk.open(knowledge).record_run_check(
        run=run,
        component_id="handoff-rejected",
        kind="handoff-disposition",
        procedure="Evaluate whether the transferred intent should become work of this run.",
        result="rejected: the proposal is no longer useful after revalidation",
        status="pass",
        evidence="revalidation showed the premise is obsolete",
    )
    assert after_disposition["state"] == "next"
    assert after_disposition["next"]["kind"] == "reading"


def test_handoff_creation_records_repository_provenance_fields(tmp_path: Path) -> None:
    knowledge = _initialized_bundle(tmp_path)
    ws = Wisk.open(knowledge)
    source = ws.start_run(
        "create a handoff",
        session_type_id="session-types/standard-experience",
    )

    created = ws.create_handoff(
        handoff_id="with-baseline",
        title="Continue later",
        created_by_run=source["run_id"],
        state="Useful work remains.",
        next_action="Revalidate and continue if still appropriate.",
    )

    assert set(created["repository"]) == {
        "repository_head",
        "repository_branch",
        "repository_dirty",
        "repository_diff_digest",
    }
