from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from wisk.bootstrap import init_repository
from wisk.mcp import mcp, wisk_start
from wisk.operations import resolve_knowledge_path


def test_fastmcp_exposes_canonical_and_legacy_start_tools() -> None:
    async def _names() -> set[str]:
        return {tool.name for tool in await mcp.list_tools()}

    names = asyncio.run(_names())
    assert {"start", "wisk_start", "wisk_start_next_session"} <= names


def test_fastmcp_start_and_cli_start_share_zero_prompt_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from wisk.cli import start as cli_start

    assert init_repository(tmp_path)["status"] == "initialized"
    monkeypatch.chdir(tmp_path)

    mcp_result = wisk_start()
    assert mcp_result["state"] == "next"

    cli_start()
    cli_result = json.loads(capsys.readouterr().out)
    assert cli_result["run"] == mcp_result["run"]
    assert cli_result["state"] == "next"
    assert cli_result["selection_reason"] == "active-run-resume"


def test_cli_legacy_positional_overrides_delegate_with_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from wisk.cli import start as cli_start

    assert init_repository(tmp_path)["status"] == "initialized"
    monkeypatch.chdir(tmp_path)

    cli_start(
        "legacy explicit task",
        "run-specs/experience",
        "session-types/standard-experience",
    )
    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert result["state"] == "next"
    assert result["run_spec"] == "run-specs/experience"
    assert result["session_type"] == "session-types/standard-experience"
    assert "Deprecated" in captured.err


def test_uninitialized_consumer_does_not_fall_back_to_knowledge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "knowledge").mkdir()
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="wisk init"):
        resolve_knowledge_path()


def test_wisk_path_remains_an_advanced_escape_hatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    explicit = tmp_path / "custom-knowledge"
    explicit.mkdir()
    monkeypatch.setenv("WISK_PATH", str(explicit))

    assert resolve_knowledge_path() == explicit.resolve()
