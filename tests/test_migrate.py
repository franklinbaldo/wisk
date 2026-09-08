"""Migration of 0.3.x consumer bundles to the 0.4.0 run schemas."""

from pathlib import Path

from wisk.migrate import migrate_bundle, migrate_document

_LEGACY_RUN = """---
type: "LoopRun"
id: "runs/legacy"
title: "Legacy run"
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


def test_migrate_drops_removed_keys_and_keeps_the_rest() -> None:
    migrated, dropped = migrate_document(_LEGACY_RUN)

    assert dropped == {"readings", "outcome", "decisions"}
    assert "readings:" not in migrated
    assert "run-readings/one" not in migrated
    assert 'task: "legacy"' in migrated
    assert migrated.endswith("# Live run\n")


def test_migrate_leaves_untouched_documents_alone() -> None:
    entry = (
        '---\ntype: "WikiEntry"\nid: "wiki/one"\nevidence:\n  - experiences/one\n---\n\n# Entry\n'
    )

    migrated, dropped = migrate_document(entry)

    assert dropped == set()
    assert migrated == entry


def test_migrate_bundle_reports_before_it_writes(tmp_path: Path) -> None:
    (tmp_path / "runs").mkdir()
    target = tmp_path / "runs" / "legacy.md"
    target.write_text(_LEGACY_RUN, encoding="utf-8")

    report = migrate_bundle(tmp_path)
    assert report["applied"] is False
    assert report["documents"] == 1
    assert report["changes"][0]["dropped"] == ["decisions", "outcome", "readings"]
    assert target.read_text(encoding="utf-8") == _LEGACY_RUN

    applied = migrate_bundle(tmp_path, apply=True)
    assert applied["applied"] is True
    assert "readings:" not in target.read_text(encoding="utf-8")

    assert migrate_bundle(tmp_path)["documents"] == 0
