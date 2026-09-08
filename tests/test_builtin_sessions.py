from __future__ import annotations

import shutil
from pathlib import Path

from wisk import Wisk

ROOT = Path(__file__).parent.parent


def _copy_bundle(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    shutil.copytree(ROOT / "specs", tmp_path / "specs")
    return tmp_path / "knowledge"


def test_builtin_session_types_declare_canonical_learning_roles() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    ids = {item["id"] for item in ws.session_types()}
    assert {
        "session-types/experience",
        "session-types/wiki",
        "session-types/skill",
        "session-types/inference",
        "session-types/wiki-maintainer",
        "session-types/skill-evolver",
        "session-types/evaluator",
        "session-types/development",
    } <= ids


def test_legacy_learning_names_specialize_canonical_roles() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    assert ws.effective_session_type("session-types/inference")["inheritance"] == [
        "session-types/work",
        "session-types/inference",
    ]
    assert ws.effective_session_type("session-types/wiki-maintainer")["inheritance"] == [
        "session-types/wiki",
        "session-types/wiki-maintainer",
    ]
    assert ws.effective_session_type("session-types/skill-evolver")["inheritance"] == [
        "session-types/skill",
        "session-types/skill-evolver",
    ]


def test_canonical_roles_are_policy_neutral() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    for session_type in (
        "session-types/work",
        "session-types/wiki",
        "session-types/skill",
    ):
        session = ws.effective_session_type(session_type)
        assert session["inheritance"] == [session_type]
        assert session["policies"] == {
            "context_policy": None,
            "access_policy": None,
            "output_policy": None,
        }


def test_inference_context_uses_skills_without_injected_wiki() -> None:
    context = Wisk.open(ROOT / "knowledge").context(
        "bootstrap repository", "session-types/inference"
    )
    assert context["skills"]
    assert context["wiki"] == []
    assert context["recent_experiences"] == []
    assert context["context_policy"]["mode"] == "curated"


def test_wiki_maintainer_keeps_pattern_as_prompt_nudge_not_type() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    session = ws.effective_session_type("session-types/wiki-maintainer")
    text = " ".join(session["nudges"])
    assert "Pattern is a writing nudge" in text
    assert "WikiEntry" in text
    assert "WikiPattern" not in ws.inventory()


def test_canonical_session_type_selects_its_own_runspec(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    result = Wisk.open(knowledge).start_run(
        "execute a task with available skills",
        session_type_id="session-types/experience",
    )
    assert result["session_type"] == "session-types/experience"
    assert result["run_spec"] == "run-specs/experience"
    requirements = {item["requirement"] for item in result["check"]["unsatisfied"]}
    assert "reading:active-skills" in requirements
    assert "goal:task-advance" in requirements


def test_evaluator_remains_optional_specialization() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    evaluator = ws.effective_session_type("session-types/evaluator")
    assert evaluator["inheritance"] == ["session-types/base", "session-types/evaluator"]
    assert "not a fourth canonical learning role" in evaluator["purpose"]
