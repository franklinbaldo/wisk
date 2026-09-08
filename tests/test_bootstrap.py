from __future__ import annotations

import json
from pathlib import Path

import pytest

import wisk.bootstrap as bootstrap
from wisk import Wisk
from wisk.bootstrap import init_repository, upgrade_repository


def _write_closed_work_runs(knowledge: Path, count: int) -> None:
    runs = knowledge / "experiences/runs"
    runs.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        stamp = f"2026-09-06T1{index}:00:00Z"
        (runs / f"consumer-work-{index}.md").write_text(
            f"""---
type: LoopRun
id: runs/consumer-work-{index}
title: Consumer work {index}
started_at: \"{stamp}\"
finished_at: \"{stamp}\"
status: closed
run_spec: run-specs/work
session_type: session-types/standard-work
task: \"Do useful repository work {index}\"
---

# Work trace {index}
""",
            encoding="utf-8",
        )


def _write_local_experience(knowledge: Path) -> Path:
    """Create a pre-0.4 consumer specialization to prove compatibility inheritance."""
    local = knowledge / "local/session-types/judicial-experience.md"
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(
        """---
type: SessionType
id: session-types/judicial-experience
title: Judicial experience
purpose: \"Do real Judicial work under the consumer contract.\"
run_spec: run-specs/experience
extends: session-types/standard-experience
nudges:
  - \"Prefer substantive Judicial work.\"
---

# Judicial experience

Pre-0.4 consumer specialization retained through the RC compatibility bridge.
""",
        encoding="utf-8",
    )
    return local


def test_init_creates_conformant_managed_consumer_bundle(tmp_path: Path) -> None:
    result = init_repository(tmp_path)

    assert result["status"] == "initialized"
    assert result["conformant"] is True
    assert result["preserved_files"] == 0
    root = tmp_path / ".wisk"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["format_version"] == 1
    assert manifest["profile"] == "standard"
    assert ".gitignore" in manifest["managed_files"]
    assert "specs/runobservation.md" in manifest["managed_files"]
    assert "specs/runskilluse.md" in manifest["managed_files"]
    assert (root / ".gitignore").read_text(encoding="utf-8") == (
        "/.gitignore\n/manifest.json\n/specs/\n/knowledge/system/\n"
    )
    assert (root / "knowledge/system/profiles/standard/session-types/work.md").is_file()
    assert (root / "knowledge/system/profiles/standard/session-types/standard-work.md").is_file()

    ws = Wisk.open(root / "knowledge")
    assert ws.next_session() is None
    started = ws.start_next_session("Do the next useful repository work")
    assert started["session_type"] == "session-types/standard-work"
    assert started["run_spec"] == "run-specs/work"
    assert started["started_at"]


def test_init_preserves_predeclared_local_specialization(tmp_path: Path) -> None:
    knowledge = tmp_path / ".wisk/knowledge"
    local = _write_local_experience(knowledge)
    before = local.read_bytes()

    result = init_repository(tmp_path)

    assert result["status"] == "initialized"
    assert result["preserved_files"] == 1
    assert local.read_bytes() == before
    ws = Wisk.open(knowledge)
    started = ws.start_next_session("Do the next useful repository work")
    assert started["session_type"] == "session-types/judicial-experience"
    assert "session-types/work" in started["session"]["inheritance"]


def test_init_preserves_versioned_runtime_knowledge(tmp_path: Path) -> None:
    knowledge = tmp_path / ".wisk/knowledge"
    local = _write_local_experience(knowledge)
    preserved = [local]
    for relative in (
        "experiences/shared.txt",
        "wiki/shared.txt",
        "skills/shared.txt",
    ):
        path = knowledge / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"keep {relative}", encoding="utf-8")
        preserved.append(path)
    before = {path: path.read_bytes() for path in preserved}

    result = init_repository(tmp_path)

    assert result["status"] == "initialized"
    assert result["preserved_files"] == 4
    assert {path: path.read_bytes() for path in preserved} == before


def test_consumer_specialization_replaces_compatibility_parent_for_scheduler(
    tmp_path: Path,
) -> None:
    init_repository(tmp_path)
    knowledge = tmp_path / ".wisk/knowledge"
    _write_local_experience(knowledge)

    ws = Wisk.open(knowledge)
    requested = ws.eligible_sessions(requested=True)
    ids = [item["session_type"] for item in requested]
    assert "session-types/judicial-experience" in ids
    assert "session-types/standard-experience" not in ids
    assert "session-types/experience" not in ids

    started = ws.start_next_session("Do the next useful repository work")
    assert started["session_type"] == "session-types/judicial-experience"
    assert started["session"]["inheritance"][-3:] == [
        "session-types/experience",
        "session-types/standard-experience",
        "session-types/judicial-experience",
    ]
    assert "session-types/work" in started["session"]["inheritance"]


def test_standard_profile_runs_wiki_then_skill_as_work_traces_accumulate(tmp_path: Path) -> None:
    init_repository(tmp_path)
    knowledge = tmp_path / ".wisk/knowledge"
    _write_closed_work_runs(knowledge, 6)

    due = Wisk.open(knowledge).next_session()
    assert due is not None
    assert due["session_type"] == "session-types/standard-wiki"
    assert due["metrics"]["threshold_value"] == 6
    assert "active-handoff" not in due["reasons"]

    wiki_run = Wisk.open(knowledge).start_next_session("Synthesize the Work corpus")
    assert wiki_run["session_type"] == "session-types/standard-wiki"

    after_wiki = Wisk.open(knowledge).next_session()
    assert after_wiki is not None
    assert after_wiki["session_type"] == "session-types/standard-skill"
    assert after_wiki["metrics"]["threshold_value"] == 6


def test_explicit_experience_alias_warns_but_remains_resolvable(tmp_path: Path) -> None:
    init_repository(tmp_path)
    knowledge = tmp_path / ".wisk/knowledge"

    result = Wisk.open(knowledge).start(
        "Compatibility work",
        session_type="session-types/experience",
    )

    assert result["session_type"] == "session-types/experience"
    assert "compatibility alias" in result["deprecation"]


def test_init_refuses_unmanaged_existing_state_without_touching_it(tmp_path: Path) -> None:
    root = tmp_path / ".wisk"
    root.mkdir()
    marker = root / "legacy.txt"
    marker.write_text("keep me", encoding="utf-8")

    result = init_repository(tmp_path)

    assert result["status"] == "unmanaged-existing-state"
    assert result["files"] == ["legacy.txt"]
    assert marker.read_text(encoding="utf-8") == "keep me"
    assert not (root / "manifest.json").exists()


def test_upgrade_preserves_consumer_owned_files(tmp_path: Path) -> None:
    init_repository(tmp_path)
    local = tmp_path / ".wisk/knowledge/local/repository-note.txt"
    local.parent.mkdir(parents=True)
    local.write_text("consumer-owned", encoding="utf-8")

    result = upgrade_repository(tmp_path)

    assert result["status"] == "upgraded"
    assert result["conformant"] is True
    assert local.read_text(encoding="utf-8") == "consumer-owned"


def test_upgrade_detects_edited_managed_file_before_writing(tmp_path: Path) -> None:
    init_repository(tmp_path)
    root = tmp_path / ".wisk"
    managed = root / "knowledge/system/canonical/session-types/experience.md"
    managed.write_text(managed.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")
    before_manifest = (root / "manifest.json").read_text(encoding="utf-8")

    result = upgrade_repository(tmp_path)

    assert result["status"] == "conflict"
    assert "knowledge/system/canonical/session-types/experience.md" in result["conflicts"]
    assert managed.read_text(encoding="utf-8").endswith("local edit\n")
    assert (root / "manifest.json").read_text(encoding="utf-8") == before_manifest


def test_upgrade_rolls_back_live_state_when_final_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_repository(tmp_path)
    root = tmp_path / ".wisk"
    managed = root / "knowledge/system/canonical/session-types/experience.md"
    before_managed = managed.read_bytes()
    before_manifest = (root / "manifest.json").read_bytes()
    real_write_manifest = bootstrap._write_manifest

    def fail_only_on_live_root(path: Path, manifest: dict[str, object]) -> None:
        if path == root:
            managed.write_text("partial write", encoding="utf-8")
            raise OSError("simulated final write failure")
        real_write_manifest(path, manifest)

    monkeypatch.setattr(bootstrap, "_write_manifest", fail_only_on_live_root)

    with pytest.raises(OSError, match="simulated final write failure"):
        upgrade_repository(tmp_path)

    assert managed.read_bytes() == before_managed
    assert (root / "manifest.json").read_bytes() == before_manifest
