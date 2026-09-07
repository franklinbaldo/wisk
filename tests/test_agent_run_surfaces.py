from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

import pytest

from wisk.mcp import (
    mcp,
    wisk_run_reading,
    wisk_start,
)

ROOT = Path(__file__).parent.parent


def _copy_bundle(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    shutil.copytree(ROOT / "specs", tmp_path / "specs")
    return tmp_path / "knowledge"


def test_mcp_exposes_scheduler_and_typed_run_writes() -> None:
    async def _names() -> set[str]:
        return {tool.name for tool in await mcp.list_tools()}

    names = asyncio.run(_names())
    assert {
        "wisk_start_next_session",
        "wisk_run_reading",
        "wisk_run_goal",
        "wisk_run_decision",
        "wisk_run_evidence",
        "wisk_run_check_record",
        "wisk_run_outcome",
    } <= names


def test_mcp_can_start_and_progress_run_at_explicit_path(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    started = wisk_start(
        "exercise MCP live-run surface",
        "run-specs/inference",
        "session-types/inference",
        str(knowledge),
    )
    result = wisk_run_reading(
        started["run_id"],
        "active-handoffs",
        "active-handoffs",
        "active handoffs",
        "knowledge/experiences/handoffs",
        "no blocking handoff is required for this test",
        str(knowledge),
    )

    assert result["run"] == started["run_id"]
    assert result["run_status"] == "in_progress"
    assert result["id"].startswith("run-readings/")


def test_cli_run_write_accepts_explicit_bundle_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from wisk.cli import run_reading

    knowledge = _copy_bundle(tmp_path)
    started = wisk_start(
        "exercise CLI live-run surface",
        "run-specs/inference",
        "session-types/inference",
        str(knowledge),
    )
    run_reading(
        started["run_id"],
        "active-skills",
        "active-skills",
        "active skills",
        "knowledge/skills/active",
        "the active skill set is available",
        path=str(knowledge),
    )

    output = json.loads(capsys.readouterr().out)
    assert output["run"] == started["run_id"]
    assert output["run_status"] == "in_progress"
