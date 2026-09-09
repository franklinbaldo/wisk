from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from wisk import Wisk

ROOT = Path(__file__).parent.parent


def _bundle(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    shutil.copytree(ROOT / "specs", tmp_path / "specs")
    return tmp_path / "knowledge"


def _write(path: Path, frontmatter: dict[str, object]) -> None:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {json.dumps(value)}")
    lines.extend(["---", "", "# Session", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def test_session_type_inheritance_appends_nudges() -> None:
    session = Wisk.open(ROOT / "knowledge").effective_session_type("session-types/development")
    assert session["inheritance"] == ["session-types/work", "session-types/development"]
    assert len(session["nudges"]) >= 4
    assert session["run_spec"] == "run-specs/wisk-development"


def test_session_type_cycle_is_rejected(tmp_path: Path) -> None:
    knowledge = _bundle(tmp_path)
    directory = knowledge / "skills" / "session-types"
    _write(
        directory / "cycle-a.md",
        {
            "type": "SessionType",
            "id": "session-types/cycle-a",
            "title": "A",
            "purpose": "cycle",
            "run_spec": "run-specs/wisk-development",
            "extends": "session-types/cycle-b",
        },
    )
    _write(
        directory / "cycle-b.md",
        {
            "type": "SessionType",
            "id": "session-types/cycle-b",
            "title": "B",
            "purpose": "cycle",
            "run_spec": "run-specs/wisk-development",
            "extends": "session-types/cycle-a",
        },
    )
    with pytest.raises(ValueError, match="inheritance cycle"):
        Wisk.open(knowledge).effective_session_type("session-types/cycle-a")


def test_missing_default_falls_back_to_an_available_session(tmp_path: Path) -> None:
    knowledge = _bundle(tmp_path)
    (knowledge / "skills" / "session-types" / "development.md").unlink()
    result = Wisk.open(knowledge).start_run("fallback session")
    assert result["session_type"] == "session-types/base"


def test_bundle_without_session_types_cannot_start(tmp_path: Path) -> None:
    knowledge = _bundle(tmp_path)
    shutil.rmtree(knowledge / "skills" / "session-types")
    with pytest.raises(ValueError, match="No SessionType"):
        Wisk.open(knowledge).start_run("no session type")
