"""Drop frontmatter keys that 0.4.0 removed from the run schemas.

A consumer bundle written against 0.3.x carries keys that normative OKF validation
now rejects. The keys were denormalized copies of relations the runtime derives from
each component's own `run` link, so removing them loses no information that the
bundle does not already hold elsewhere.
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

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):")


def _document_type(frontmatter_lines: list[str]) -> str:
    for line in frontmatter_lines:
        match = _KEY.match(line)
        if match and match.group(1) == "type":
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


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


def migrate_document(content: str) -> tuple[str, set[str]]:
    """Return the document without removed keys, plus the keys actually dropped."""
    match = _FRONTMATTER.match(content)
    if not match:
        return content, set()
    frontmatter_lines = match.group(1).split("\n")
    removed = REMOVED_KEYS.get(_document_type(frontmatter_lines))
    if not removed:
        return content, set()
    kept, dropped = _strip_keys(frontmatter_lines, removed)
    if not dropped:
        return content, set()
    return "---\n" + "\n".join(kept) + "\n---\n" + match.group(2), dropped


def migrate_bundle(path: str | Path = "knowledge", *, apply: bool = False) -> dict[str, Any]:
    """Report, and optionally apply, the 0.4.0 frontmatter removals across a bundle."""
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    changes: list[dict[str, Any]] = []
    for source in sorted(root.rglob("*.md")):
        original = source.read_text(encoding="utf-8")
        migrated, dropped = migrate_document(original)
        if not dropped:
            continue
        changes.append(
            {
                "path": str(source.relative_to(root)),
                "dropped": sorted(dropped),
            }
        )
        if apply:
            source.write_text(migrated, encoding="utf-8", newline="\n")

    return {
        "bundle": str(root),
        "applied": apply,
        "documents": len(changes),
        "changes": changes,
    }


__all__ = ["REMOVED_KEYS", "migrate_bundle", "migrate_document"]
