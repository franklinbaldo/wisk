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


def test_partial_run_requires_handoff_and_future_run_archives_it(tmp_path: Path) -> None:
    knowledge_path = _temp_bundle(tmp_path)
    ws = Wisk.open(knowledge_path)
    source = ws.start_run("wisk handoff development", "run-specs/wisk-development")
    source_run = source["run_id"]

    _write_concept(
        knowledge_path / "experiences" / "runs" / "partial-outcome.md",
        {
            "type": "RunOutcome",
            "id": "run-outcomes/handoff-source",
            "run": source_run,
            "result_state": "red",
            "work_status": "partial",
            "summary": "handoff capability is only partially implemented",
            "next_move": "continue the Handoff lifecycle implementation",
        },
    )

    before = Wisk.open(knowledge_path).check_run(source_run)
    assert "handoff" in {item["requirement"] for item in before["unsatisfied"]}

    ws = Wisk.open(knowledge_path)
    created = ws.create_handoff(
        handoff_id="handoff-runtime",
        title="Finish Handoff runtime",
        created_by_run=source_run,
        state="The type and RED contract exist; lifecycle implementation remains.",
        next_action="Implement create/list/continue and make checks GREEN.",
        references=["#38", "src/wisk/handoff.py"],
    )
    assert created["id"] == "handoffs/handoff-runtime"
    assert created["status"] == "active"

    after = Wisk.open(knowledge_path).check_run(source_run)
    assert "handoff" not in {item["requirement"] for item in after["unsatisfied"]}
    assert after["active_handoffs_created"] == 1

    context = Wisk.open(knowledge_path).context("finish handoff runtime")
    assert context["active_handoffs"][0]["id"] == "handoffs/handoff-runtime"
    assert context["active_handoffs"][0]["next_action"].startswith("Implement create")

    continuing = Wisk.open(knowledge_path).start_run(
        "finish handoff runtime", "run-specs/wisk-development"
    )
    continuing_run = continuing["run_id"]
    assert continuing["active_handoffs"][0]["id"] == "handoffs/handoff-runtime"

    archived = Wisk.open(knowledge_path).continue_handoff(
        handoff="handoffs/handoff-runtime",
        continued_by_run=continuing_run,
        resolution="The later run adopted the handoff and continued its implementation.",
    )
    assert archived == {
        "id": "handoffs/handoff-runtime",
        "status": "archived",
        "continued_by_run": continuing_run,
    }
    assert Wisk.open(knowledge_path).active_handoffs() == []

    handoff_doc = (knowledge_path / "experiences" / "handoffs" / "handoff-runtime.md").read_text(
        encoding="utf-8"
    )
    assert 'status: "archived"' in handoff_doc
    assert f'continued_by_run: "{continuing_run}"' in handoff_doc
    assert "archived_at:" in handoff_doc
    assert "resolution:" in handoff_doc


def test_handoff_mcp_surface_executes_full_lifecycle(tmp_path: Path) -> None:
    from wisk.mcp import (
        wisk_handoff_continue,
        wisk_handoff_create,
        wisk_handoffs,
    )

    knowledge_path = _temp_bundle(tmp_path)
    source = Wisk.open(knowledge_path).start_run("source handoff", "run-specs/wisk-development")
    continuing = Wisk.open(knowledge_path).start_run(
        "continue handoff", "run-specs/wisk-development"
    )

    created = wisk_handoff_create(
        handoff_id="mcp-handoff",
        title="Continue through MCP",
        created_by_run=source["run_id"],
        state="Source run left material work.",
        next_action="Resume it through the MCP surface.",
        references=["#38"],
        path=str(knowledge_path),
    )
    assert created["status"] == "active"

    active = wisk_handoffs("MCP handoff", path=str(knowledge_path))
    assert active[0]["id"] == "handoffs/mcp-handoff"

    archived = wisk_handoff_continue(
        handoff="handoffs/mcp-handoff",
        continued_by_run=continuing["run_id"],
        resolution="The continuing run resumed the MCP handoff.",
        path=str(knowledge_path),
    )
    assert archived["status"] == "archived"
    assert wisk_handoffs(path=str(knowledge_path)) == []


def test_handoff_rejects_invalid_continuation(tmp_path: Path) -> None:
    knowledge_path = _temp_bundle(tmp_path)
    ws = Wisk.open(knowledge_path)
    source = ws.start_run("source handoff", "run-specs/wisk-development")
    source_run = source["run_id"]
    ws.create_handoff(
        handoff_id="same-run",
        title="Cannot continue in same run",
        created_by_run=source_run,
        state="Work remains.",
        next_action="A future run must resume it.",
    )

    with pytest.raises(ValueError, match="later LoopRun"):
        Wisk.open(knowledge_path).continue_handoff(
            handoff="handoffs/same-run",
            continued_by_run=source_run,
            resolution="This must be rejected.",
        )


def test_complete_run_does_not_require_handoff(tmp_path: Path) -> None:
    knowledge_path = _temp_bundle(tmp_path)
    ws = Wisk.open(knowledge_path)
    started = ws.start_run("wisk development", "run-specs/wisk-development")
    run_id = started["run_id"]

    _write_concept(
        knowledge_path / "experiences" / "runs" / "complete-outcome.md",
        {
            "type": "RunOutcome",
            "id": "run-outcomes/complete",
            "run": run_id,
            "result_state": "green",
            "work_status": "complete",
            "summary": "the run-owned work is complete",
            "next_move": "a future run may choose another useful goal",
        },
    )

    result = Wisk.open(knowledge_path).check_run(run_id)
    assert "handoff" not in {item["requirement"] for item in result["unsatisfied"]}
