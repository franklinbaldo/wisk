from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from wisk import Wisk
from wisk.bootstrap import init_repository

ROOT = Path(__file__).parent.parent


def _copy_bundle(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    shutil.copytree(ROOT / "specs", tmp_path / "specs")
    return tmp_path / "knowledge"


def test_raw_trace_requires_declared_okf_schemas(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge)
    run_id = ws.start_run("typed Raw trace", "run-specs/wisk-development")["run_id"]

    (tmp_path / "specs" / "runobservation.schema.sql").unlink()

    with pytest.raises(ValueError, match="RunObservation"):
        ws.run_trace(run_id)


def test_declared_type_without_instances_is_an_empty_collection(tmp_path: Path) -> None:
    """okf-parser materializes a relation only once an instance exists.

    A Work run that recorded no explicit decision is well-formed, so the declared
    RunDecision type must read back as zero records rather than raising.
    """
    init_repository(tmp_path)
    knowledge = tmp_path / ".wisk/knowledge"
    run = str(
        Wisk.open(knowledge).start(
            "Work without an explicit decision",
            session_type="session-types/standard-work",
        )["run"]
    )

    trace = Wisk.open(knowledge).run_trace(run)

    assert trace["decisions"] == []
