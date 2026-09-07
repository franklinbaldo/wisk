"""Canonical public operations shared by FastMCP and terminal adapters."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from wisk import Wisk


def resolve_knowledge_path(path: str | Path | None = None) -> Path:
    """Resolve an explicit/managed Wisk bundle without silently guessing consumer state."""
    if path is not None:
        return Path(path).resolve()

    configured = os.environ.get("WISK_PATH", "").strip()
    if configured:
        return Path(configured).resolve()

    managed = Path(".wisk") / "knowledge"
    if managed.is_dir():
        return managed.resolve()

    # Wisk's own repository is the one supported dogfood exception. Require positive
    # repository structure instead of treating every uninitialized consumer's
    # `knowledge/` directory as a Wisk bundle.
    dogfood = Path("knowledge")
    if (
        dogfood.is_dir()
        and Path("specs").is_dir()
        and (Path("src") / "wisk").is_dir()
        and Path("pyproject.toml").is_file()
    ):
        return dogfood.resolve()

    raise ValueError("Wisk is not initialized in this repository; run `wisk init` first.")


def runtime(path: str | Path | None = None) -> Wisk:
    """Open the resolved Wisk runtime for a public operation."""
    return Wisk.open(resolve_knowledge_path(path))


def start(
    task: str | None = None,
    *,
    session_type: str | None = None,
    run_spec: str | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Start or resume useful work through RFC 0006's canonical operation."""
    result = runtime(path).start(
        task,
        session_type=session_type,
        run_spec=run_spec,
    )
    # Temporary compatibility alias for callers of the pre-RFC 0006 Python/MCP surface.
    # The canonical operation envelope uses `run`; remove `run_id` after the deprecation window.
    if result.get("run") is not None:
        result.setdefault("run_id", result["run"])
    return result
