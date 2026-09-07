"""Cross-session Handoff lifecycle for the Wisk runtime."""

from __future__ import annotations

import hashlib
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from okf_parser import load_bundle
from okf_parser.service import check_bundle

from wisk.runtime import Wisk as BaseWisk

_HANDOFF_STATUS_ACTIVE = "active"
_HANDOFF_STATUS_ARCHIVED = "archived"
_TERMINAL_GOAL_STATUSES = frozenset({"achieved", "carried_forward"})
_HANDOFF_ENVIRONMENT_CHECK = "handoff-environment"
_HANDOFF_DISPOSITION_CHECK = "handoff-disposition"


class HandoffWisk(BaseWisk):
    """Wisk runtime with resumable cross-session handoffs."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> HandoffWisk:
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
                    "created_at": str(fm.get("created_at") or ""),
                    "created_by_run": str(fm.get("created_by_run") or ""),
                    "target_session_type": str(fm.get("target_session_type") or ""),
                    "state": str(fm.get("state") or ""),
                    "next_action": str(fm.get("next_action") or ""),
                    "references": references,
                    "goals": goals,
                    "repository_head": str(fm.get("repository_head") or ""),
                    "repository_branch": str(fm.get("repository_branch") or ""),
                    "repository_dirty": bool(fm.get("repository_dirty")),
                    "repository_diff_digest": str(fm.get("repository_diff_digest") or ""),
                    "relevant": relevant,
                }
            )
        return sorted(
            handoffs,
            key=lambda item: (not item["relevant"], item["created_at"], item["id"]),
        )

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
                raise ValueError(f"Handoff goal belongs to another run: {goal_identifier}")
            canonical_goal = str(goal_fm.get("id") or goal["id"])
            if canonical_goal not in linked_goals:
                linked_goals.append(canonical_goal)

        canonical_id = f"handoffs/{slug}"
        directory = self.root_path / "handoffs"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{slug}.md"
        if path.exists():
            raise FileExistsError(path)

        baseline = self._repository_baseline()
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
            **baseline,
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
        return {
            "id": canonical_id,
            "path": str(path),
            "status": _HANDOFF_STATUS_ACTIVE,
            "repository": baseline,
        }

    def attach_handoff_to_run(self, *, handoff: str, run: str) -> dict[str, Any]:
        """Bind an active Handoff to its fresh consumer LoopRun without archiving it."""
        handoff_record = self._find_record("Handoff", handoff)
        handoff_fm = handoff_record["frontmatter"]
        if str(handoff_fm.get("status") or "") != _HANDOFF_STATUS_ACTIVE:
            raise ValueError(f"Handoff is not active: {handoff}")
        run_record = self._find_record("LoopRun", run)
        run_fm = dict(run_record["frontmatter"])
        run_id = str(run_fm.get("id") or run_record["id"])
        canonical_handoff = str(handoff_fm.get("id") or handoff_record["id"])
        path = self.root_path / run_record["path"]
        previous = path.read_text(encoding="utf-8")
        run_fm["resumed_handoff"] = canonical_handoff
        body = self._body_from_document(previous)
        path.write_text(self._render_markdown(run_fm, body), encoding="utf-8")
        try:
            self._require_conformant_bundle()
        except Exception:
            path.write_text(previous, encoding="utf-8")
            self._reload()
            raise
        self._reload()
        return {"run": run_id, "resumed_handoff": canonical_handoff}

    def continue_handoff(
        self,
        *,
        handoff: str,
        continued_by_run: str,
        resolution: str,
    ) -> dict[str, Any]:
        """Archive a handoff and identify the LoopRun that resolved its continuation."""
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
        result = super().context(task)
        result["active_handoffs"] = self.active_handoffs(task)
        return result

    def start_run(self, task: str, run_spec_id: str | None = None) -> dict[str, Any]:
        result = super().start_run(task, run_spec_id)
        result["active_handoffs"] = self.active_handoffs(task)
        return result

    def check_run(self, run_id_or_path: str) -> dict[str, Any]:
        """Require terminal goals plus handoff revalidation/disposition when applicable."""
        result = super().check_run(run_id_or_path)
        run = self._find_record("LoopRun", run_id_or_path)
        run_fm = run["frontmatter"]
        run_id = str(run_fm.get("id") or run["id"])
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
        resumed_handoff = str(run_fm.get("resumed_handoff") or "")
        if resumed_handoff:
            checks = self._run_components("RunCheck", run_id)
            by_kind = {
                str(item["frontmatter"].get("kind") or ""): item["frontmatter"]
                for item in checks
            }
            environment = by_kind.get(_HANDOFF_ENVIRONMENT_CHECK)
            if environment is None:
                lifecycle_requirements.append(
                    {
                        "requirement": f"check:{_HANDOFF_ENVIRONMENT_CHECK}",
                        "kind": _HANDOFF_ENVIRONMENT_CHECK,
                        "handoff": resumed_handoff,
                        "message": (
                            "Revalidate and document repository/environment state against the "
                            "handoff baseline before relying on prior continuation instructions."
                        ),
                    }
                )
            elif str(environment.get("status") or "") != "pass":
                lifecycle_requirements.append(
                    {
                        "requirement": f"check:{_HANDOFF_ENVIRONMENT_CHECK}:resolved",
                        "kind": _HANDOFF_ENVIRONMENT_CHECK,
                        "handoff": resumed_handoff,
                        "observed": str(environment.get("status") or ""),
                        "message": "Resolve repository/environment drift before continuing the handoff.",
                    }
                )

            disposition = by_kind.get(_HANDOFF_DISPOSITION_CHECK)
            if disposition is None:
                lifecycle_requirements.append(
                    {
                        "requirement": f"check:{_HANDOFF_DISPOSITION_CHECK}",
                        "kind": _HANDOFF_DISPOSITION_CHECK,
                        "handoff": resumed_handoff,
                        "expected": ["accepted", "reframed", "rejected"],
                        "message": (
                            "Evaluate the transferred handoff goals and document whether they are "
                            "accepted, reframed, or rejected with rationale/evidence."
                        ),
                    }
                )
            elif str(disposition.get("status") or "") != "pass":
                lifecycle_requirements.append(
                    {
                        "requirement": f"check:{_HANDOFF_DISPOSITION_CHECK}:resolved",
                        "kind": _HANDOFF_DISPOSITION_CHECK,
                        "handoff": resumed_handoff,
                        "observed": str(disposition.get("status") or ""),
                        "message": "Resolve the handoff disposition before continuing or closing.",
                    }
                )

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
                                f"Resolve RunGoal '{goal_id}' as achieved or carried_forward "
                                "before closing the LoopRun."
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
        result["resumed_handoff"] = resumed_handoff or None
        result["active_handoffs_created"] = len(active_for_run)
        result["handoffs_created"] = len(handoffs_for_run)
        return result

    def _repository_baseline(self) -> dict[str, Any]:
        repo = self._repository_root()
        if repo is None:
            return {
                "repository_head": "",
                "repository_branch": "",
                "repository_dirty": False,
                "repository_diff_digest": "",
            }

        def git(*args: str) -> str:
            result = subprocess.run(
                ["git", "-C", str(repo), *args],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else ""

        head = git("rev-parse", "HEAD")
        branch = git("rev-parse", "--abbrev-ref", "HEAD")
        status = git("status", "--porcelain=v1", "--untracked-files=all")
        diff_digest = (
            f"sha256:{hashlib.sha256(status.encode('utf-8')).hexdigest()}" if status else ""
        )
        return {
            "repository_head": head,
            "repository_branch": branch,
            "repository_dirty": bool(status),
            "repository_diff_digest": diff_digest,
        }

    def _repository_root(self) -> Path | None:
        candidates = [self.root_path, *self.root_path.parents]
        for candidate in candidates:
            if (candidate / ".git").exists():
                return candidate
        return None

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
