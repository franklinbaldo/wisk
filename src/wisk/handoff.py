"""Cross-session Handoff lifecycle for the Wisk runtime."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from okf_parser import load_bundle
from okf_parser.service import check_bundle

from wisk.runtime import Wisk as BaseWisk

_HANDOFF_STATUS_ACTIVE = "active"
_HANDOFF_STATUS_ARCHIVED = "archived"
_TERMINAL_GOAL_STATUSES = frozenset({"achieved", "carried_forward"})


class HandoffWisk(BaseWisk):
    """Wisk runtime with resumable cross-session handoffs."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> HandoffWisk:
        """Open an OKF bundle while preserving the Handoff-enabled runtime type."""
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    def active_handoffs(self, task: str | None = None) -> list[dict[str, Any]]:
        """List active handoffs, ranking task-relevant work first."""
        keywords = {
            word for word in re.findall(r"[a-z0-9_-]+", (task or "").lower()) if len(word) > 2
        }
        handoffs: list[dict[str, Any]] = []
        for record in self._records("Handoff"):
            fm = record["frontmatter"]
            if str(fm.get("status") or "") != _HANDOFF_STATUS_ACTIVE:
                continue
            canonical_id = str(fm.get("id") or record["id"])
            references = [str(item) for item in fm.get("references", [])]
            goals = [str(item) for item in fm.get("goals", [])]
            corpus = " ".join(
                [
                    canonical_id,
                    record["title"],
                    str(fm.get("state") or ""),
                    str(fm.get("next_action") or ""),
                    *references,
                    *goals,
                ]
            ).lower()
            relevant = any(word in corpus for word in keywords) if keywords else True
            handoffs.append(
                {
                    "id": canonical_id,
                    "title": record["title"],
                    "path": record["path"],
                    "created_by_run": str(fm.get("created_by_run") or ""),
                    "target_session_type": str(fm.get("target_session_type") or ""),
                    "state": str(fm.get("state") or ""),
                    "next_action": str(fm.get("next_action") or ""),
                    "references": references,
                    "goals": goals,
                    "relevant": relevant,
                }
            )
        return sorted(handoffs, key=lambda item: (not item["relevant"], item["id"]))

    def create_handoff(
        self,
        *,
        handoff_id: str,
        title: str,
        created_by_run: str,
        state: str,
        next_action: str,
        references: list[str] | None = None,
        goals: list[str] | None = None,
        target_session_type: str | None = None,
    ) -> dict[str, Any]:
        """Persist active unfinished work emitted by one LoopRun."""
        run = self._find_record("LoopRun", created_by_run)
        run_id = str(run["frontmatter"].get("id") or run["id"])
        slug = self._slug(handoff_id.rsplit("/", 1)[-1])
        if not slug:
            raise ValueError("handoff_id must contain a usable identifier")
        if not title.strip() or not state.strip() or not next_action.strip():
            raise ValueError("title, state and next_action must not be empty")

        linked_goals: list[str] = []
        for goal_identifier in goals or []:
            goal = self._find_record("RunGoal", goal_identifier)
            goal_fm = goal["frontmatter"]
            if str(goal_fm.get("run") or "") != run_id:
                msg = f"Handoff goal belongs to another run: {goal_identifier}"
                raise ValueError(msg)
            canonical_goal = str(goal_fm.get("id") or goal["id"])
            if canonical_goal not in linked_goals:
                linked_goals.append(canonical_goal)

        canonical_id = f"handoffs/{slug}"
        directory = self.root_path / "handoffs"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{slug}.md"
        if path.exists():
            raise FileExistsError(path)

        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        frontmatter: dict[str, Any] = {
            "type": "Handoff",
            "id": canonical_id,
            "title": title,
            "created_at": now,
            "status": _HANDOFF_STATUS_ACTIVE,
            "created_by_run": run_id,
            "state": state,
            "next_action": next_action,
            "references": references or [],
            "goals": linked_goals,
        }
        if target_session_type:
            frontmatter["target_session_type"] = target_session_type
        path.write_text(self._render_markdown(frontmatter, "# Handoff\n"), encoding="utf-8")
        try:
            self._require_conformant_bundle()
        except Exception:
            path.unlink(missing_ok=True)
            self._reload()
            raise
        self._reload()
        return {"id": canonical_id, "path": str(path), "status": _HANDOFF_STATUS_ACTIVE}

    def continue_handoff(
        self,
        *,
        handoff: str,
        continued_by_run: str,
        resolution: str,
    ) -> dict[str, Any]:
        """Archive a handoff and identify the LoopRun that resumed it."""
        self._find_record("LoopRun", continued_by_run)
        record = self._find_record("Handoff", handoff)
        frontmatter = dict(record["frontmatter"])
        canonical_id = str(frontmatter.get("id") or record["id"])
        if str(frontmatter.get("status") or "") != _HANDOFF_STATUS_ACTIVE:
            raise ValueError(f"Handoff is already archived: {canonical_id}")
        created_by_run = str(frontmatter.get("created_by_run") or "")
        if continued_by_run == created_by_run:
            raise ValueError("continued_by_run must identify a later LoopRun")
        if not resolution.strip():
            raise ValueError("resolution must not be empty")

        path = self.root_path / record["path"]
        previous = path.read_text(encoding="utf-8")
        body = self._body_from_document(previous)
        frontmatter.update(
            {
                "status": _HANDOFF_STATUS_ARCHIVED,
                "continued_by_run": continued_by_run,
                "archived_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "resolution": resolution,
            }
        )
        path.write_text(self._render_markdown(frontmatter, body), encoding="utf-8")
        try:
            self._require_conformant_bundle()
        except Exception:
            path.write_text(previous, encoding="utf-8")
            self._reload()
            raise
        self._reload()
        return {
            "id": canonical_id,
            "status": _HANDOFF_STATUS_ARCHIVED,
            "continued_by_run": continued_by_run,
        }

    def context(self, task: str) -> dict[str, Any]:
        """Include active handoffs alongside learned and contract context."""
        result = super().context(task)
        result["active_handoffs"] = self.active_handoffs(task)
        return result

    def start_run(self, task: str, run_spec_id: str | None = None) -> dict[str, Any]:
        """Start a run and surface resumable work before the agent proceeds."""
        result = super().start_run(task, run_spec_id)
        result["active_handoffs"] = self.active_handoffs(task)
        return result

    def check_run(self, run_id_or_path: str) -> dict[str, Any]:
        """Require every run-owned goal to reach a terminal, accountable state."""
        result = super().check_run(run_id_or_path)
        run = self._find_record("LoopRun", run_id_or_path)
        run_id = str(run["frontmatter"].get("id") or run["id"])
        goals = self._run_components("RunGoal", run_id)
        handoffs_for_run = [
            item
            for item in self._records("Handoff")
            if str(item["frontmatter"].get("created_by_run") or "") == run_id
        ]
        active_for_run = [
            item
            for item in handoffs_for_run
            if str(item["frontmatter"].get("status") or "") == _HANDOFF_STATUS_ACTIVE
        ]

        lifecycle_requirements: list[dict[str, Any]] = []
        if not goals:
            lifecycle_requirements.append(
                {
                    "requirement": "goal:terminal",
                    "kind": "goal-state",
                    "message": "Resolve at least one RunGoal before closing the LoopRun.",
                }
            )
        else:
            linked_goals = {
                str(goal_id)
                for handoff in handoffs_for_run
                for goal_id in handoff["frontmatter"].get("goals", [])
            }
            for goal in goals:
                goal_fm = goal["frontmatter"]
                goal_id = str(goal_fm.get("id") or goal["id"])
                status = str(goal_fm.get("status") or "")
                if status not in _TERMINAL_GOAL_STATUSES:
                    lifecycle_requirements.append(
                        {
                            "requirement": f"goal-state:{goal_id}",
                            "kind": "goal-state",
                            "goal": goal_id,
                            "observed": status,
                            "expected": sorted(_TERMINAL_GOAL_STATUSES),
                            "message": (
                                f"Resolve RunGoal '{goal_id}' as achieved or "
                                "carried_forward before closing the LoopRun."
                            ),
                        }
                    )
                elif status == "carried_forward" and goal_id not in linked_goals:
                    lifecycle_requirements.append(
                        {
                            "requirement": f"handoff:{goal_id}",
                            "kind": "handoff",
                            "goal": goal_id,
                            "message": (
                                "Create a Handoff from this run that explicitly lists "
                                f"carried-forward goal '{goal_id}'."
                            ),
                        }
                    )

        outcomes = self._run_components("RunOutcome", run_id)
        if outcomes:
            work_status = str(outcomes[-1]["frontmatter"].get("work_status") or "")
            if work_status == "partial" and not handoffs_for_run:
                lifecycle_requirements.append(
                    {
                        "requirement": "handoff",
                        "kind": "handoff",
                        "message": "Record a Handoff for material work left to a future LoopRun.",
                    }
                )

        if lifecycle_requirements:
            result["unsatisfied"].extend(lifecycle_requirements)
            result["conformant"] = False
            if result["next_action"].get("kind") == "complete":
                result["next_action"] = dict(lifecycle_requirements[0])
        result["active_handoffs_created"] = len(active_for_run)
        result["handoffs_created"] = len(handoffs_for_run)
        return result

    def _require_conformant_bundle(self) -> None:
        report = check_bundle(
            str(self.root_path),
            require_spec="../specs/{slug}.md",
            normative_spec=True,
        )
        if not bool(report["conformant"]):
            diagnostics = report.get("diagnostics", [])
            raise ValueError(f"Handoff write would make the OKF bundle invalid: {diagnostics!r}")

    @staticmethod
    def _body_from_document(content: str) -> str:
        parts = content.split("---", 2)
        if len(parts) < 3:
            return "# Handoff\n"
        body = parts[2].lstrip("\n")
        return body or "# Handoff\n"
