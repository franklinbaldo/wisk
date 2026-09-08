"""Migrate 0.3.x knowledge toward RFC 0007's 0.4 Work-trace model.

The migration is deliberately conservative. It removes denormalized run backlinks,
adds explicit `started_at` when a legacy LoopRun has `timestamp`, and reports legacy
Experience documents without deleting or fabricating their historical provenance.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

REMOVED_KEYS: dict[str, frozenset[str]] = {
    "LoopRun": frozenset(
        {
            "readings",
            "goals",
            "decisions",
            "evidence",
            "checks",
            "outcome",
            "skills_consulted",
            "experiences_recorded",
            "proposals_generated",
        }
    ),
    "RunOutcome": frozenset({"goals_advanced", "evidence", "checks", "experiences_recorded"}),
    "RunEvidence": frozenset({"decision"}),
    "RunDecision": frozenset({"evidence"}),
    "RunSpec": frozenset({"allowed_entry_states"}),
}

# Pre-0.4 aliases are no longer auto-selected, so an active Handoff still targeting one
# would never be continued. Retarget it at the Work specialization that replaces it.
RETARGETED_SESSION_TYPES = {
    "session-types/experience": "session-types/work",
    "session-types/standard-experience": "session-types/standard-work",
    "session-types/inference": "session-types/work",
}

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):")


def _document_type(frontmatter_lines: list[str]) -> str:
    for line in frontmatter_lines:
        match = _KEY.match(line)
        if match and match.group(1) == "type":
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def _scalar(frontmatter_lines: list[str], key: str) -> str | None:
    prefix = f"{key}:"
    for line in frontmatter_lines:
        if line.startswith(prefix):
            value = line.split(":", 1)[1].strip()
            return value or None
    return None


def _strip_keys(
    frontmatter_lines: list[str],
    removed: frozenset[str],
) -> tuple[list[str], set[str]]:
    kept: list[str] = []
    dropped: set[str] = set()
    skipping = False
    for line in frontmatter_lines:
        match = _KEY.match(line)
        if match:
            key = match.group(1)
            skipping = key in removed
            if skipping:
                dropped.add(key)
        elif skipping and not line.startswith((" ", "\t", "-")):
            skipping = False
        if not skipping:
            kept.append(line)
    return kept, dropped


def _add_started_at(frontmatter_lines: list[str]) -> tuple[list[str], bool]:
    """Copy the legacy objective start timestamp without guessing a finish timestamp."""
    if _document_type(frontmatter_lines) != "LoopRun":
        return frontmatter_lines, False
    if _scalar(frontmatter_lines, "started_at") is not None:
        return frontmatter_lines, False
    timestamp = _scalar(frontmatter_lines, "timestamp")
    if timestamp is None:
        return frontmatter_lines, False

    result: list[str] = []
    inserted = False
    for line in frontmatter_lines:
        result.append(line)
        if line.startswith("timestamp:"):
            result.append(f"started_at: {timestamp}")
            inserted = True
    return result, inserted


def _retarget_handoff(frontmatter_lines: list[str]) -> tuple[list[str], str | None]:
    """Point an active Handoff at the Work session type that replaces its 0.3.x target."""
    if _document_type(frontmatter_lines) != "Handoff":
        return frontmatter_lines, None
    current = _scalar(frontmatter_lines, "target_session_type")
    if current is None:
        return frontmatter_lines, None
    replacement = RETARGETED_SESSION_TYPES.get(current.strip().strip('"').strip("'"))
    if replacement is None:
        return frontmatter_lines, None

    result = [
        f'target_session_type: "{replacement}"' if line.startswith("target_session_type:") else line
        for line in frontmatter_lines
    ]
    return result, replacement


def migrate_document(content: str) -> tuple[str, set[str]]:
    """Return one document migrated toward 0.4rc1 plus the transformations applied."""
    match = _FRONTMATTER.match(content)
    if not match:
        return content, set()
    frontmatter_lines = match.group(1).split("\n")
    document_type = _document_type(frontmatter_lines)
    removed = REMOVED_KEYS.get(document_type, frozenset())
    kept, dropped = _strip_keys(frontmatter_lines, removed)
    kept, added_start = _add_started_at(kept)
    kept, retargeted = _retarget_handoff(kept)
    changes = {f"dropped:{key}" for key in dropped}
    if added_start:
        changes.add("added:started_at")
    if retargeted:
        changes.add(f"retargeted:{retargeted}")
    if not changes:
        return content, set()
    return "---\n" + "\n".join(kept) + "\n---\n" + match.group(2), changes


def migrate_bundle(path: str | Path = "knowledge", *, apply: bool = False) -> dict[str, Any]:
    """Report, and optionally apply, RFC 0007-safe 0.4 RC transformations."""
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    changes: list[dict[str, Any]] = []
    legacy_experiences: list[dict[str, Any]] = []
    for source in sorted(root.rglob("*.md")):
        original = source.read_text(encoding="utf-8")
        match = _FRONTMATTER.match(original)
        if match:
            lines = match.group(1).split("\n")
            if _document_type(lines) == "Experience":
                legacy_experiences.append(
                    {
                        "path": str(source.relative_to(root)),
                        "run": _scalar(lines, "run"),
                        "skill_used": _scalar(lines, "skill_used"),
                        "skill_version": _scalar(lines, "skill_version"),
                    }
                )

        migrated, transformations = migrate_document(original)
        if not transformations:
            continue
        changes.append(
            {
                "path": str(source.relative_to(root)),
                "transformations": sorted(transformations),
            }
        )
        if apply:
            source.write_text(migrated, encoding="utf-8", newline="\n")

    return {
        "bundle": str(root),
        "target": "0.4.0rc1",
        "applied": apply,
        "documents": len(changes),
        "changes": changes,
        "legacy_experiences": legacy_experiences,
        "legacy_experience_policy": (
            "preserved-read-only: provenance remains queryable during the RC; "
            "new standard Work runs use RunSkillUse instead of creating Experience summaries"
        ),
    }


__all__ = ["REMOVED_KEYS", "migrate_bundle", "migrate_document"]
