from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import pytest

from wisk import Wisk
from wisk.mcp import mcp

ROOT = Path(__file__).parent.parent


def _copy_bundle(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    shutil.copytree(ROOT / "knowledge", repo / "knowledge")
    shutil.copytree(ROOT / "specs", repo / "specs")
    return repo / "knowledge"


def _experience_kwargs() -> dict[str, str]:
    return {
        "experience_id": "exp-contract-guided-recording",
        "title": "Record learning from a contract-guided run",
        "timestamp": "2026-09-05T18:15:00Z",
        "status": "success",
        "task": "Restore Experience Recording on the contract-guided runtime",
        "context": "PR #23 reanchored after the RunSpec/LoopRun pivot",
        "run": "runs/20260905-contract-guided-runtime",
        "body": (
            "# Experience Recording Dogfood\n\n"
            "## Context & Intent\n"
            "Make learned Experience a native output of contract-guided execution.\n\n"
            "## Action & Observed Output\n"
            "The runtime writes one validated Experience and refreshes its OKF bundle.\n\n"
            "## Findings\n"
            "Experience can retain provenance to the LoopRun that produced the learning.\n"
        ),
    }


def test_preview_experience_is_pure_and_links_run(tmp_path: Path) -> None:
    knowledge_path = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge_path)

    preview = ws.preview_experience(**_experience_kwargs())

    assert preview["id"] == "exp-contract-guided-recording"
    assert preview["path"] == "experiences/records/exp-contract-guided-recording.md"
    assert preview["content"].startswith('---\ntype: "Experience"\n')
    assert 'run: "runs/20260905-contract-guided-runtime"' in preview["content"]
    assert "# Experience Recording Dogfood" in preview["content"]
    assert not (knowledge_path / preview["path"]).exists()


def test_record_experience_writes_valid_okf_and_refreshes_runtime(tmp_path: Path) -> None:
    knowledge_path = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge_path)
    before = ws.inventory()["Experience"]
    preview = ws.preview_experience(**_experience_kwargs())

    result = ws.record_experience(**_experience_kwargs())
    result_path = result["path"]
    assert isinstance(result_path, str)

    target = knowledge_path / result_path
    assert result == {
        "id": "exp-contract-guided-recording",
        "path": "experiences/records/exp-contract-guided-recording.md",
        "written": True,
    }
    assert target.read_text(encoding="utf-8") == preview["content"]
    assert ws.inventory()["Experience"] == before + 1
    assert Wisk.open(knowledge_path).inventory()["Experience"] == before + 1


def test_fastmcp_experience_tools_registered() -> None:
    async def _check() -> None:
        tools = await mcp.list_tools()
        names = {tool.name for tool in tools}
        assert "wisk_experience_preview" in names
        assert "wisk_experience_record" in names

    asyncio.run(_check())


def test_fastmcp_experience_tools_execute(tmp_path: Path) -> None:
    from wisk.mcp import wisk_experience_preview, wisk_experience_record

    knowledge_path = _copy_bundle(tmp_path)
    kwargs = _experience_kwargs()

    preview = wisk_experience_preview(path=str(knowledge_path), **kwargs)
    assert preview["id"] == kwargs["experience_id"]
    assert not (knowledge_path / preview["path"]).exists()

    result = wisk_experience_record(path=str(knowledge_path), **kwargs)
    assert result["written"] is True
    result_path = result["path"]
    assert isinstance(result_path, str)
    assert (knowledge_path / result_path).exists()


def test_cli_experience_preview_and_record(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from wisk.cli import experience_preview, experience_record

    knowledge_path = _copy_bundle(tmp_path)
    kwargs = _experience_kwargs()

    experience_preview(path=str(knowledge_path), **kwargs)
    captured = capsys.readouterr()
    assert 'type: "Experience"' in captured.out
    assert kwargs["experience_id"] in captured.out

    experience_record(path=str(knowledge_path), **kwargs)
    captured = capsys.readouterr()
    assert f"Recorded Experience {kwargs['experience_id']}" in captured.out
    assert (knowledge_path / f"experiences/records/{kwargs['experience_id']}.md").exists()
