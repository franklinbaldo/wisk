from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from wisk import Wisk

ROOT = Path(__file__).parent.parent
NOW = datetime(2026, 9, 5, 20, 0, tzinfo=UTC)


def _copy_bundle(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    shutil.copytree(ROOT / "specs", tmp_path / "specs")
    return tmp_path / "knowledge"


def test_on_demand_session_is_explainable_but_not_auto_selected() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    automatic = ws.session_eligibility("session-types/inference", now=NOW)
    requested = ws.session_eligibility("session-types/inference", now=NOW, requested=True)
    assert "explicit-request" not in automatic["reasons"]
    assert requested["eligible"] is True
    assert "explicit-request" in requested["reasons"]


def test_canonical_roles_do_not_duplicate_consumer_cadence() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    for session_type in (
        "session-types/experience",
        "session-types/wiki",
        "session-types/skill",
    ):
        automatic = ws.session_eligibility(session_type, now=NOW)
        requested = ws.session_eligibility(session_type, now=NOW, requested=True)
        assert automatic["eligible"] is False
        assert automatic["blockers"] == ["no-cadence-policy"]
        assert requested["eligible"] is True
        assert requested["reasons"] == ["explicit-request"]


def test_new_experiences_activate_wiki_maintainer() -> None:
    result = Wisk.open(ROOT / "knowledge").session_eligibility(
        "session-types/wiki-maintainer", now=NOW
    )
    assert result["eligible"] is True
    assert "threshold" in result["reasons"] or "max-delay" in result["reasons"]
    assert result["metrics"]["threshold_value"] >= 3


def test_targeted_handoff_activates_compatible_session(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    ws = Wisk.open(knowledge)
    source = ws.start_run("source", session_type_id="session-types/development")
    ws.create_handoff(
        handoff_id="evaluate-next",
        title="Evaluate candidate",
        created_by_run=source["run_id"],
        target_session_type="session-types/evaluator",
        state="Candidate is ready for independent evaluation.",
        next_action="Run the evaluator contract.",
    )
    result = Wisk.open(knowledge).session_eligibility(
        "session-types/evaluator", now=datetime.now(UTC)
    )
    assert result["eligible"] is True
    assert "active-handoff" in result["reasons"]
    assert result["metrics"]["targeted_handoffs"] == 1


def test_parent_targeted_handoff_activates_leaf_specialization(tmp_path: Path) -> None:
    knowledge = _copy_bundle(tmp_path)
    child = knowledge / "skills/session-types/judicial-evaluator.md"
    child.write_text(
        """---
type: SessionType
id: session-types/judicial-evaluator
title: Judicial evaluator
purpose: \"Evaluate under Judicial-specific guidance.\"
run_spec: run-specs/evaluation
extends: session-types/evaluator
nudges:
  - \"Apply the Judicial specialization.\"
---

# Judicial evaluator

Consumer-owned specialization of the evaluator role.
""",
        encoding="utf-8",
    )

    ws = Wisk.open(knowledge)
    source = ws.start_run("source", session_type_id="session-types/development")
    ws.create_handoff(
        handoff_id="evaluate-specialized-next",
        title="Evaluate candidate in consumer",
        created_by_run=source["run_id"],
        target_session_type="session-types/evaluator",
        state="Candidate is ready for evaluation.",
        next_action="Run the specialized evaluator contract.",
    )

    reopened = Wisk.open(knowledge)
    eligible = reopened.eligible_sessions(now=datetime.now(UTC))
    ids = [item["session_type"] for item in eligible]
    assert "session-types/judicial-evaluator" in ids
    assert "session-types/evaluator" not in ids
    result = reopened.session_eligibility(
        "session-types/judicial-evaluator",
        now=datetime.now(UTC),
    )
    assert "active-handoff" in result["reasons"]
    assert result["metrics"]["targeted_handoffs"] == 1


def test_next_session_is_deterministic_by_priority() -> None:
    ws = Wisk.open(ROOT / "knowledge")
    eligible = ws.eligible_sessions(now=NOW)
    assert eligible == sorted(eligible, key=lambda item: (-item["priority"], item["session_type"]))
    assert ws.next_session(now=NOW) == (eligible[0] if eligible else None)
