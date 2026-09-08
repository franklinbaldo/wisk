from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

import pytest
from okf_parser import load_bundle

from wisk import Wisk, __version__
from wisk.mcp import mcp
from wisk.models import generate_pydantic_code, get_schema_contracts

ROOT = Path(__file__).parent.parent


def _write_concept(path: Path, frontmatter: dict[str, object]) -> None:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(["---", "", "# Test concept", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _temp_bundle(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    shutil.copytree(ROOT / "specs", tmp_path / "specs")
    return tmp_path / "knowledge"


def test_version() -> None:
    assert __version__ == "0.4.0rc1"


def test_bundle_conformance() -> None:
    knowledge_path = ROOT / "knowledge"
    bundle = load_bundle(knowledge_path)
    count = bundle.concepts.count().execute()
    assert count >= 4

    concept_types = set(bundle.concepts.select("concept_type").distinct().execute()["concept_type"])
    assert "Experience" in concept_types
    assert "WikiEntry" in concept_types
    assert "AgentSkill" in concept_types
    assert "RunSpec" in concept_types
    assert "SessionType" in concept_types
    assert "ContextPolicy" in concept_types
    assert "AccessPolicy" in concept_types
    assert "OutputPolicy" in concept_types
    assert "CadencePolicy" in concept_types


def test_wisk_runtime_inventory_and_context() -> None:
    knowledge_path = ROOT / "knowledge"
    ws = Wisk.open(knowledge_path)
    inv = ws.inventory()
    assert inv["Experience"] >= 1
    assert inv["WikiEntry"] >= 1
    assert inv["AgentSkill"] >= 1
    assert inv["RunSpec"] >= 1
    assert inv["SessionType"] >= 2
    assert inv["CadencePolicy"] >= 5

    ctx = ws.context(task="wisk development")
    assert ctx["task"] == "wisk development"
    assert ctx["session_type"] == "session-types/development"
    assert ctx["context_policy"]["id"] == "context-policies/development"
    assert any(s["id"] == "run-specs/wisk-development" for s in ctx["run_specs"])
    assert "active_handoffs" in ctx

    bootstrap_ctx = ws.context(task="bootstrap repository setup")
    assert len(bootstrap_ctx["skills"]) >= 1
    assert any(s["id"] == "skill-bootstrap-repository" for s in bootstrap_ctx["skills"])
    assert len(bootstrap_ctx["recent_experiences"]) >= 1


def test_run_start_is_incomplete_and_contract_guided(tmp_path: Path) -> None:
    knowledge_path = _temp_bundle(tmp_path)
    ws = Wisk.open(knowledge_path)

    started = ws.start_run(
        "wisk development",
        "run-specs/wisk-development",
    )

    assert started["status"] == "scaffold"
    assert started["session_type"] == "session-types/development"
    assert started["session"]["inheritance"] == ["session-types/base", "session-types/development"]
    assert Path(started["path"]).exists()
    assert "experiences/runs" in started["path"]
    assert "active_handoffs" in started
    check = started["check"]
    assert check["conformant"] is False
    requirements = {item["requirement"] for item in check["unsatisfied"]}
    assert "reading:repository-guide" in requirements
    assert "reading:active-handoffs" in requirements
    assert "goal:project-advance" in requirements
    assert "evidence:change" in requirements
    assert "check:tests" in requirements
    assert "outcome" in requirements
    assert check["next_action"] == {
        "kind": "reading",
        "requirement": "reading:repository-guide",
        "expected": "repository-guide",
        "message": "Record RunReading kind 'repository-guide'.",
    }


def test_run_check_turns_green_when_contract_is_satisfied(tmp_path: Path) -> None:
    knowledge_path = _temp_bundle(tmp_path)
    ws = Wisk.open(knowledge_path)
    started = ws.start_run("wisk development", "run-specs/wisk-development")
    run_id = started["run_id"]
    runs = knowledge_path / "experiences" / "runs"

    for index, kind in enumerate(
        [
            "repository-guide",
            "open-issues",
            "open-prs",
            "okf-knowledge",
            "recent-runs",
            "active-handoffs",
        ],
        start=1,
    ):
        _write_concept(
            runs / f"reading-{index}.md",
            {
                "type": "RunReading",
                "id": f"run-readings/{index}",
                "run": run_id,
                "kind": kind,
                "subject": kind,
                "reference": f"ref:{kind}",
                "finding": f"finding for {kind}",
            },
        )

    _write_concept(
        runs / "goal.md",
        {
            "type": "RunGoal",
            "id": "run-goals/1",
            "run": run_id,
            "kind": "project-advance",
            "goal": "advance the runtime",
            "rationale": "exercise the execution contract",
            "success_signal": "contract becomes satisfied",
            "status": "achieved",
        },
    )

    for index, kind in enumerate(["change", "verification"], start=1):
        _write_concept(
            runs / f"evidence-{index}.md",
            {
                "type": "RunEvidence",
                "id": f"run-evidence/{index}",
                "run": run_id,
                "kind": kind,
                "reference": f"ref:{kind}",
                "summary": f"evidence for {kind}",
            },
        )

    for index, kind in enumerate(["okf", "tests"], start=1):
        _write_concept(
            runs / f"check-{index}.md",
            {
                "type": "RunCheck",
                "id": f"run-checks/{index}",
                "run": run_id,
                "kind": kind,
                "procedure": f"verify {kind}",
                "result": "passed",
                "status": "pass",
            },
        )

    _write_concept(
        runs / "outcome.md",
        {
            "type": "RunOutcome",
            "id": "run-outcomes/1",
            "run": run_id,
            "result_state": "green",
            "work_status": "complete",
            "summary": "the run contract is satisfied",
            "next_move": "continue with the next useful run",
        },
    )

    result = Wisk.open(knowledge_path).check_run(run_id)
    assert result["structural"]["conformant"] is True
    assert result["unsatisfied"] == []
    assert result["conformant"] is True
    assert result["next_action"] == {
        "kind": "complete",
        "requirement": None,
        "message": "Run satisfies its pinned RunSpec.",
    }


def test_fastmcp_tools_registered() -> None:
    async def _check() -> None:
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "wisk_inventory" in tool_names
        assert "wisk_context" in tool_names
        assert "wisk_start" in tool_names
        assert "wisk_check" in tool_names
        assert "wisk_handoffs" in tool_names
        assert "wisk_handoff_create" in tool_names
        assert "wisk_handoff_continue" in tool_names
        assert "wisk_session_eligibility" in tool_names
        assert "wisk_next_session" in tool_names

    asyncio.run(_check())


def test_pydantic_schema_contracts_derivation() -> None:
    knowledge_path = ROOT / "knowledge"
    code = generate_pydantic_code(knowledge_path)
    assert "class AgentSkillConcept(BaseModel):" in code
    assert "class ExperienceConcept(BaseModel):" in code
    assert "class WikiEntryConcept(BaseModel):" in code
    assert "class RunSpecConcept(BaseModel):" in code
    assert "class HandoffConcept(BaseModel):" in code
    assert "class SessionTypeConcept(BaseModel):" in code
    assert "class ContextPolicyConcept(BaseModel):" in code
    assert "class AccessPolicyConcept(BaseModel):" in code
    assert "class OutputPolicyConcept(BaseModel):" in code
    assert "class CadencePolicyConcept(BaseModel):" in code

    contracts = get_schema_contracts(knowledge_path)
    contract_types = {c.concept_type for c in contracts}
    assert contract_types >= {
        "AgentSkill",
        "Experience",
        "WikiEntry",
        "RunSpec",
        "Handoff",
        "SessionType",
        "ContextPolicy",
        "AccessPolicy",
        "OutputPolicy",
        "CadencePolicy",
    }


def test_mcp_tool_execution() -> None:
    from wisk.mcp import wisk_context, wisk_inventory

    inv = wisk_inventory()
    assert inv["Experience"] >= 1
    assert inv["RunSpec"] >= 1

    ctx = wisk_context("wisk development")
    assert ctx["task"] == "wisk development"
    assert len(ctx["run_specs"]) >= 1
    assert "active_handoffs" in ctx


def test_cli_execution(capsys: pytest.CaptureFixture[str]) -> None:
    from wisk.cli import context, info

    info()
    captured = capsys.readouterr()
    assert "wisk runtime v0.4.0rc1" in captured.out

    context("bootstrap")
    captured = capsys.readouterr()
    assert "Context for: bootstrap" in captured.out
    assert "Active handoffs" in captured.out
    assert "Skills found" in captured.out
