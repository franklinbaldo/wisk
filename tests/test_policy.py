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


def _write(path: Path, frontmatter: dict[str, object]) -> None:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(["---", "", "# Test policy", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def test_default_output_policy_keeps_three_primary_namespaces() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    assert ws.output_path("Experience") == "experiences/records"
    assert ws.output_path("LoopRun") == "experiences/runs"
    assert ws.output_path("Handoff") == "experiences/handoffs"
    assert ws.output_path("WikiEntry") == "wiki/entries"
    assert ws.output_path("AgentSkill") == "skills/active"
    assert ws.output_path("SessionType") == "skills/session-types"


def test_advisory_policy_explains_without_filtering() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    context = ws.context("wisk development", "session-types/development")
    assert context["context_policy"]["mode"] == "advisory"
    assert context["access_policy"]["mode"] == "advisory"
    assert context["skills"]
    assert context["wiki"]


def test_curated_policy_filters_injected_context_without_claiming_access_enforcement(
    tmp_path: Path,
) -> None:
    knowledge = _copy_bundle(tmp_path)
    _write(
        knowledge / "skills" / "policies" / "context" / "skills-only.md",
        {
            "type": "ContextPolicy",
            "id": "context-policies/skills-only",
            "title": "Skills only",
            "mode": "curated",
            "include": ["skills", "run-specs"],
            "exclude": ["wiki", "experiences", "handoffs"],
            "instructions": ["Use active skills; wiki is outside this session context."],
        },
    )
    _write(
        knowledge / "skills" / "session-types" / "curated.md",
        {
            "type": "SessionType",
            "id": "session-types/curated-test",
            "title": "Curated test session",
            "purpose": "Exercise context curation",
            "run_spec": "run-specs/wisk-development",
            "extends": "session-types/base",
            "context_policy": "context-policies/skills-only",
            "access_policy": "access-policies/development",
        },
    )

    context = Wisk.open(knowledge).context("bootstrap", "session-types/curated-test")
    assert context["skills"]
    assert context["wiki"] == []
    assert context["recent_experiences"] == []
    assert context["active_handoffs"] == []
    assert context["access_policy"]["mode"] == "advisory"
