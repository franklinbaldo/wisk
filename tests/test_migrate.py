"""Migration of 0.3.x consumer bundles to the 0.4 RC Work-trace model."""

from pathlib import Path

from wisk.migrate import migrate_bundle, migrate_document

_LEGACY_RUN = """---
type: "LoopRun"
id: "runs/legacy"
title: "Legacy run"
timestamp: "2026-09-01T10:00:00Z"
status: "closed"
run_spec: "run-specs/wisk-development"
task: "legacy"
readings:
  - run-readings/one
  - run-readings/two
outcome: "run-outcomes/legacy"
decisions:
  - run-decisions/one
---

# Live run
"""

_LEGACY_EXPERIENCE = """---
type: Experience
id: experience-legacy
title: Legacy experience
timestamp: "2026-09-01T11:00:00Z"
status: success
run: runs/legacy
skill_used: skill-example
skill_version: "1.2.0"
---

# Legacy experience
"""


def test_migrate_drops_backlinks_and_adds_explicit_start_time() -> None:
    migrated, transformations = migrate_document(_LEGACY_RUN)

    assert transformations == {
        "dropped:readings",
        "dropped:outcome",
        "dropped:decisions",
        "added:started_at",
    }
    assert "readings:" not in migrated
    assert "run-readings/one" not in migrated
    assert 'task: "legacy"' in migrated
    assert 'started_at: "2026-09-01T10:00:00Z"' in migrated
    assert migrated.endswith("# Live run\n")


def test_migrate_leaves_unrelated_documents_alone() -> None:
    entry = '---\ntype: "WikiEntry"\nid: "wiki/one"\nevidence:\n  - runs/one\n---\n\n# Entry\n'

    migrated, transformations = migrate_document(entry)

    assert transformations == set()
    assert migrated == entry


def test_migrate_bundle_reports_before_it_writes_and_preserves_legacy_experience(
    tmp_path: Path,
) -> None:
    (tmp_path / "runs").mkdir()
    target = tmp_path / "runs" / "legacy.md"
    target.write_text(_LEGACY_RUN, encoding="utf-8")
    legacy_experience = tmp_path / "legacy-experience.md"
    legacy_experience.write_text(_LEGACY_EXPERIENCE, encoding="utf-8")

    report = migrate_bundle(tmp_path)
    assert report["target"] == "0.4.0rc1"
    assert report["applied"] is False
    assert report["documents"] == 1
    assert report["changes"][0]["transformations"] == [
        "added:started_at",
        "dropped:decisions",
        "dropped:outcome",
        "dropped:readings",
    ]
    assert report["legacy_experiences"] == [
        {
            "path": "legacy-experience.md",
            "run": "runs/legacy",
            "skill_used": "skill-example",
            "skill_version": '"1.2.0"',
        }
    ]
    assert target.read_text(encoding="utf-8") == _LEGACY_RUN
    assert legacy_experience.read_text(encoding="utf-8") == _LEGACY_EXPERIENCE

    applied = migrate_bundle(tmp_path, apply=True)
    assert applied["applied"] is True
    migrated = target.read_text(encoding="utf-8")
    assert "readings:" not in migrated
    assert "started_at:" in migrated
    assert legacy_experience.read_text(encoding="utf-8") == _LEGACY_EXPERIENCE

    assert migrate_bundle(tmp_path)["documents"] == 0


def test_migrate_retargets_a_handoff_away_from_a_pre_04_alias() -> None:
    """An alias target is never auto-selected, so an unmigrated handoff would be stranded."""
    handoff = (
        '---\ntype: "Handoff"\nid: "handoffs/resume"\nstatus: "active"\n'
        'target_session_type: "session-types/standard-experience"\n---\n\n# Handoff\n'
    )

    migrated, changes = migrate_document(handoff)

    assert changes == {"retargeted:session-types/standard-work"}
    assert 'target_session_type: "session-types/standard-work"' in migrated
    assert "standard-experience" not in migrated


def test_migrate_leaves_an_unrecognized_handoff_target_alone() -> None:
    handoff = (
        '---\ntype: "Handoff"\nid: "handoffs/local"\nstatus: "active"\n'
        'target_session_type: "session-types/judicial-work"\n---\n\n# Handoff\n'
    )

    migrated, changes = migrate_document(handoff)

    assert changes == set()
    assert migrated == handoff


def test_migrate_leaves_an_archived_handoff_as_history() -> None:
    """An archived handoff records which session type actually continued the work."""
    handoff = (
        '---\ntype: "Handoff"\nid: "handoffs/done"\nstatus: "archived"\n'
        'target_session_type: "session-types/experience"\n'
        'continued_by_run: "runs/legacy"\n---\n\n# Handoff\n'
    )

    migrated, changes = migrate_document(handoff)

    assert changes == set()
    assert migrated == handoff


def test_migrate_drops_a_multiline_flow_collection_without_orphaning_its_terminator() -> None:
    """A dangling `]` would make the applied frontmatter unparseable."""
    run = (
        '---\ntype: "LoopRun"\nid: "runs/flow"\ntimestamp: "2026-09-01T10:00:00Z"\n'
        'goals: [\n  "run-goals/one",\n  "run-goals/two"\n]\nstatus: "closed"\n---\n\n# Run\n'
    )

    migrated, changes = migrate_document(run)

    assert changes == {"dropped:goals", "added:started_at"}
    assert migrated == (
        '---\ntype: "LoopRun"\nid: "runs/flow"\ntimestamp: "2026-09-01T10:00:00Z"\n'
        'started_at: "2026-09-01T10:00:00Z"\nstatus: "closed"\n---\n\n# Run\n'
    )
    assert "]" not in migrated.split("---\n")[1]


def test_migrate_does_not_treat_a_bracket_inside_a_quoted_scalar_as_a_flow_collection() -> None:
    run = (
        '---\ntype: "LoopRun"\nid: "runs/quoted"\n'
        'goals: ["run-goals/one [draft]"]\nstatus: "closed"\n---\n\n# Run\n'
    )

    migrated, changes = migrate_document(run)

    assert changes == {"dropped:goals"}
    assert migrated == ('---\ntype: "LoopRun"\nid: "runs/quoted"\nstatus: "closed"\n---\n\n# Run\n')
