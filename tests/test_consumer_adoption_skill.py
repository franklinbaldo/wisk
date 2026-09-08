from __future__ import annotations

from pathlib import Path

from wisk.bootstrap import init_repository


def test_bootstrap_installs_consumer_adoption_skill_with_role_boundaries(tmp_path: Path) -> None:
    result = init_repository(tmp_path)

    assert result["status"] == "initialized"
    root = tmp_path / ".wisk/knowledge/system/profiles/standard"
    skill = root / "skills/adopt-wisk-consumer.md"
    assert skill.is_file()

    text = skill.read_text(encoding="utf-8")
    paper_title = (
        "WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution"
    )
    assert paper_title in text
    assert "https://arxiv.org/abs/2608.27454" in text
    assert "Work / Worker" in text and "Raw Layer" in text
    assert "Wiki / Wiki Maintainer" in text and "consolidates recurrence" in text
    assert "Skill / Skill Evolver" in text and "atomic procedural intervention" in text
    assert "Never put instructions" in text


def test_standard_work_leaves_synthesis_to_wiki(tmp_path: Path) -> None:
    """The Worker records the raw trace; it must not be told to synthesize knowledge."""
    init_repository(tmp_path)

    root = tmp_path / ".wisk/knowledge/system/profiles/standard/session-types"
    session = (root / "standard-work.md").read_text(encoding="utf-8")

    assert "leave cross-run synthesis to Wiki" in session
    assert "RunSkillUse" not in session or "skill/version actually used" in session
    assert "WikiEntry" not in session

    alias = (root / "standard-experience.md").read_text(encoding="utf-8")
    assert "deprecated compatibility alias" in alias.lower()
    assert "session-types/standard-work" in alias
