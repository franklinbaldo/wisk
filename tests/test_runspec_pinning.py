from __future__ import annotations

import json
import shutil
from pathlib import Path

from wisk import Wisk

ROOT = Path(__file__).parent.parent


def _copy_bundle(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    shutil.copytree(ROOT / "specs", tmp_path / "specs")
    return tmp_path / "knowledge"


def test_new_run_pins_complete_runspec_snapshot(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge)
    started = ws.start_run(
        "pin the governing contract",
        "run-specs/wisk-development",
    )

    run = Wisk.open(knowledge)._find_record("LoopRun", started["run_id"])
    frontmatter = run["frontmatter"]
    snapshot = json.loads(str(frontmatter["run_spec_snapshot"]))

    assert frontmatter["run_spec_version"] == "1.1.0"
    assert str(frontmatter["run_spec_digest"]).startswith("sha256:")
    assert snapshot["id"] == "run-specs/wisk-development"
    assert snapshot["required_goal_kinds"] == ["project-advance"]
    assert "path" not in snapshot
    assert "inheritance" not in snapshot
    assert started["check"]["run_spec_pinned"] is True


def test_parent_spec_appends_requirements_into_pinned_contract(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    child = knowledge / "skills/run-specs/judicial-skill.md"
    child.write_text(
        """---
type: RunSpec
id: run-specs/judicial-skill
title: Judicial skill evolution
version: \"1.0.0\"
status: active
parent_spec: run-specs/skill
required_reading_kinds: []
required_goal_kinds: []
required_evidence_kinds: []
required_check_kinds:
  - proportionality
completion_notes: \"Add Judicial proportionality without copying the parent contract.\"
---

# Judicial skill evolution

Consumer specialization of the canonical Skill RunSpec.
""",
        encoding="utf-8",
    )

    ws = Wisk.open(knowledge)
    effective = ws.effective_run_spec("run-specs/judicial-skill")
    assert effective["inheritance"] == ["run-specs/skill", "run-specs/judicial-skill"]
    assert effective["required_goal_kinds"] == ["evolve-skill"]
    assert effective["required_evidence_kinds"] == ["intervention"]
    assert effective["required_check_kinds"] == ["lineage", "proportionality"]
    assert effective["allowed_result_states"] == [
        "proposed",
        "refined",
        "promoted",
        "rejected",
        "no-change",
        "partial",
        "blocked",
    ]

    started = ws.start_run("evolve Judicial procedure", "run-specs/judicial-skill")
    run = Wisk.open(knowledge)._find_record("LoopRun", started["run_id"])
    snapshot = json.loads(str(run["frontmatter"]["run_spec_snapshot"]))
    assert snapshot["id"] == "run-specs/judicial-skill"
    assert snapshot["required_check_kinds"] == ["lineage", "proportionality"]
    assert "path" not in snapshot
    assert "inheritance" not in snapshot
    requirements = {item["requirement"] for item in started["check"]["unsatisfied"]}
    assert "check:lineage" in requirements
    assert "check:proportionality" in requirements


def test_check_run_uses_snapshot_after_runspec_changes(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    started = Wisk.open(knowledge).start_run(
        "historical contract stability",
        "run-specs/wisk-development",
    )

    spec_path = knowledge / "skills" / "run-specs" / "wisk-development.md"
    current = spec_path.read_text(encoding="utf-8")
    changed = current.replace(
        "required_goal_kinds:\n  - project-advance",
        "required_goal_kinds:\n  - project-advance\n  - retroactive-new-goal",
    )
    spec_path.write_text(changed, encoding="utf-8")

    result = Wisk.open(knowledge).check_run(started["run_id"])
    requirements = {item["requirement"] for item in result["unsatisfied"]}

    assert result["run_spec_pinned"] is True
    assert result["run_spec_version"] == "1.1.0"
    assert "goal:project-advance" in requirements
    assert "goal:retroactive-new-goal" not in requirements


def test_tampered_runspec_snapshot_fails_contract_check(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    started = Wisk.open(knowledge).start_run(
        "detect snapshot tampering",
        "run-specs/wisk-development",
    )

    ws = Wisk.open(knowledge)
    run = ws._find_record("LoopRun", started["run_id"])
    path = knowledge / run["path"]
    digest = str(run["frontmatter"]["run_spec_digest"])
    replacement = "sha256:" + ("0" * 64)
    path.write_text(path.read_text(encoding="utf-8").replace(digest, replacement), encoding="utf-8")

    result = Wisk.open(knowledge).check_run(started["run_id"])

    assert result["conformant"] is False
    assert result["next_action"]["kind"] == "contract"
    assert result["next_action"]["requirement"] == "run-spec-snapshot"
