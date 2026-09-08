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


def _close_work_runs(knowledge: Path, count: int) -> None:
    """Accumulate closed Work traces, which is what makes Wiki synthesis eligible."""
    for index in range(count):
        run = str(
            Wisk.open(knowledge).start(
                f"Judicial work {index}",
                session_type="session-types/standard-work",
            )["run"]
        )
        runtime = Wisk.open(knowledge)
        for kind, reference, finding in (
            ("active-handoffs", "wisk:handoffs", "No prior operational responsibility."),
            ("active-skills", "skill-adopt-wisk-consumer", "The adoption skill applies."),
        ):
            runtime.record_run_reading(
                run=run,
                component_id=kind,
                kind=kind,
                subject=kind,
                reference=reference,
                finding=finding,
            )
        goal = runtime.record_run_goal(
            run=run,
            component_id="task-advance",
            kind="task-advance",
            goal=f"Advance judicial work {index}.",
            rationale="The consumer needs accumulated raw traces before synthesis.",
            success_signal="The trace closes with verified execution evidence.",
        )
        runtime.record_run_evidence(
            run=run,
            component_id="execution",
            kind="execution",
            reference=f"judicial-work-{index}",
            summary=f"Observed useful Judicial work {index}.",
            goal=str(goal["id"]),
        )
        runtime.record_run_check(
            run=run,
            component_id="verification",
            kind="verification",
            procedure="Confirm the observed effect against execution evidence.",
            result="Evidence supports the claimed effect.",
            status="pass",
        )
        runtime.update_run_goal_status(run=run, goal=str(goal["id"]), status="achieved")
        runtime.record_run_outcome(
            run=run,
            component_id="complete",
            result_state="success",
            work_status="complete",
            summary=f"Judicial work {index} is complete.",
            next_move="A later Wiki session may compare this trace with the others.",
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
    _close_work_runs(knowledge, 6)

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
