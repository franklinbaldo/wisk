from __future__ import annotations

from pathlib import Path

from wisk import Wisk
from wisk.bootstrap import init_repository

JUDICIAL_EXPERIENCE = """---
type: SessionType
id: session-types/judicial-experience
title: Judicial Experience
purpose: \"Fazer trabalho útil no Judicial com evidência reutilizável.\"
run_spec: run-specs/experience
extends: session-types/standard-experience
nudges:
  - \"Priorize avanço substantivo no Judicial.\"
---

# Judicial Experience

Consumer specialization of canonical Experience.
"""

JUDICIAL_SKILL_SPEC = """---
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
completion_notes: \"Exija evidência para justificar custo permanente.\"
---

# Judicial Skill RunSpec

Adds only proportionality to the canonical Skill contract.
"""

JUDICIAL_SKILL = """---
type: SessionType
id: session-types/judicial-skill
title: Judicial Skill
purpose: \"Evoluir procedimento reutilizável com evidência real.\"
run_spec: run-specs/judicial-skill
extends: session-types/standard-skill
nudges:
  - \"Compare o ganho esperado com o custo permanente da intervenção.\"
---

# Judicial Skill

Consumer specialization of canonical Skill.
"""


def _write_judicial_local_bundle(repository: Path) -> Path:
    local = repository / ".wisk/knowledge/local"
    (local / "session-types").mkdir(parents=True)
    (local / "run-specs").mkdir(parents=True)
    (local / "session-types/judicial-experience.md").write_text(
        JUDICIAL_EXPERIENCE,
        encoding="utf-8",
    )
    (local / "run-specs/judicial-skill.md").write_text(
        JUDICIAL_SKILL_SPEC,
        encoding="utf-8",
    )
    (local / "session-types/judicial-skill.md").write_text(
        JUDICIAL_SKILL,
        encoding="utf-8",
    )
    return repository / ".wisk/knowledge"


def _record_experiences(knowledge: Path, count: int) -> None:
    for index in range(count):
        Wisk.open(knowledge).record_experience(
            experience_id=f"judicial-exp-{index}",
            title=f"Judicial experience {index}",
            timestamp=f"2026-09-06T1{index}:00:00+00:00",
            status="success",
            body=f"# Experience {index}\n\nObserved useful Judicial work {index}.",
        )


def test_judicial_consumer_keeps_only_local_specializations(tmp_path: Path) -> None:
    knowledge = _write_judicial_local_bundle(tmp_path)

    initialized = init_repository(tmp_path)

    assert initialized["status"] == "initialized"
    assert initialized["conformant"] is True
    assert initialized["preserved_files"] == 3

    ws = Wisk.open(knowledge)
    started = ws.start_next_session("Faça o melhor avanço substantivo possível no Judicial")
    assert started["session_type"] == "session-types/judicial-experience"
    assert started["run_spec"] == "run-specs/experience"

    effective_skill = ws.effective_run_spec("run-specs/judicial-skill")
    assert effective_skill["inheritance"] == [
        "run-specs/skill",
        "run-specs/judicial-skill",
    ]
    assert effective_skill["required_check_kinds"] == [
        "lineage",
        "proportionality",
    ]
    assert effective_skill["required_evidence_kinds"] == ["intervention"]


def test_judicial_consumer_uses_canonical_wiki_then_local_skill(
    tmp_path: Path,
) -> None:
    knowledge = _write_judicial_local_bundle(tmp_path)
    init_repository(tmp_path)
    _record_experiences(knowledge, 6)

    first_due = Wisk.open(knowledge).next_session()
    assert first_due is not None
    assert first_due["session_type"] == "session-types/standard-wiki"

    wiki_run = Wisk.open(knowledge).start_next_session("Synthesize accumulated evidence")
    assert wiki_run["session_type"] == "session-types/standard-wiki"

    second_due = Wisk.open(knowledge).next_session()
    assert second_due is not None
    assert second_due["session_type"] == "session-types/judicial-skill"

    skill_run = Wisk.open(knowledge).start_next_session("Evolve reusable Judicial procedure")
    assert skill_run["session_type"] == "session-types/judicial-skill"
    assert skill_run["run_spec"] == "run-specs/judicial-skill"
    requirements = {item["requirement"] for item in skill_run["check"]["unsatisfied"]}
    assert "check:lineage" in requirements
    assert "check:proportionality" in requirements
