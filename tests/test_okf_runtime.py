from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from wisk import Wisk

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
