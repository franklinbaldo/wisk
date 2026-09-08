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
    assert count > 0


def test_pydantic_generation() -> None:
    code = generate_pydantic_code(ROOT / "specs")
    assert "class LoopRun" in code


def test_schema_contracts() -> None:
    contracts = get_schema_contracts(ROOT / "specs")
    assert "LoopRun" in contracts


def test_mcp_server_exists() -> None:
    assert mcp is not None


def test_public_runtime_alias() -> None:
    assert Wisk is not None


@pytest.mark.asyncio
async def test_asyncio_available() -> None:
    await asyncio.sleep(0)
