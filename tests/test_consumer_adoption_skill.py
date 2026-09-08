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
    assert "Experience" in text and "truthful raw episodic evidence" in text
    assert "Wiki" in text and "synthesizes durable knowledge" in text
    assert "Skill" in text and "procedural" in text
    assert "Never put instructions" in text


def test_standard_experience_explicitly_forbids_wiki_or_skill_synthesis(tmp_path: Path) -> None:
    init_repository(tmp_path)

    session = (
        tmp_path / ".wisk/knowledge/system/profiles/standard/session-types/standard-experience.md"
    ).read_text(encoding="utf-8")

    assert "truthful raw episodic evidence" in session
    assert "do not synthesize it into WikiEntry or evolve AgentSkill" in session
    assert "Wiki owns synthesis and Skill owns procedural change" in session
