"""Typed writes for progressing a live LoopRun through its contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from okf_parser import load_bundle

from wisk.pinning import PinnedWisk

_COMPONENT_PREFIXES = {
    "RunReading": "run-readings",
    "RunGoal": "run-goals",
    "RunDecision": "run-decisions",
    "RunEvidence": "run-evidence",
    "RunCheck": "run-checks",
    "RunOutcome": "run-outcomes",
}
_COMPONENT_FIELDS = {
    "RunReading": "readings",
    "RunGoal": "goals",
    "RunDecision": "decisions",
    "RunEvidence": "evidence",
    "RunCheck": "checks",
    "RunOutcome": "outcome",
}
_COMPONENT_LABELS = {
    "RunReading": "reading",
    "RunGoal": "goal",
    "RunDecision": "decision",
    "RunEvidence": "evidence",
    "RunCheck": "check",
    "RunOutcome": "outcome",
}
_GOAL_STATUSES = frozenset({"planned", "active", "advanced", "achieved", "carried_forward"})
_CHECK_STATUSES = frozenset({"pass", "fail", "inconclusive"})
_WORK_STATUSES = frozenset({"complete", "partial"})


class LiveRunWisk(PinnedWisk):
    """Pinned runtime that can persist typed state into a live LoopRun."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> LiveRunWisk:
        """Open a bundle while preserving the live-run runtime type."""
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    def record_run_reading(
        self,
        *,
        run: str,
        component_id: str,
        kind: str,
        subject: str,
        reference: str,
        finding: str,
    ) -> dict[str, Any]:
        """Record one provenance-bearing reading consulted by a live run."""
        return self._record_run_component(
            "RunReading",
            run,
            component_id,
            {
                "kind": kind,
                "subject": subject,
                "reference": reference,
                "finding": finding,
            },
        )

    def record_run_goal(
        self,
        *,
        run: str,
        component_id: str,
        kind: str,
        goal: str,
        rationale: str,
        success_signal: str,
        status: str = "active",
    ) -> dict[str, Any]:
        """Record one observable goal owned by a live run."""
        self._require_enum("status", status, _GOAL_STATUSES)
        return self._record_run_component(
            "RunGoal",
            run,
            component_id,
            {
                "kind": kind,
                "goal": goal,
                "rationale": rationale,
                "success_signal": success_signal,
                "status": status,
            },
        )

    def update_run_goal_status(
        self,
        *,
        run: str,
        goal: str,
        status: str,
    ) -> dict[str, Any]:
        """Move one existing RunGoal to the state actually reached by its live run."""
        self._require_enum("status", status, _GOAL_STATUSES)
        run_record = self._find_record("LoopRun", run)
        run_fm = run_record["frontmatter"]
        run_id = str(run_fm.get("id") or run_record["id"])
        if str(run_fm.get("status") or "") == "closed":
            raise ValueError(f"LoopRun is already closed: {run_id}")

        goal_record = self._find_record("RunGoal", goal)
        goal_fm = dict(goal_record["frontmatter"])
        goal_id = str(goal_fm.get("id") or goal_record["id"])
        if str(goal_fm.get("run") or "") != run_id:
            raise ValueError(f"RunGoal does not belong to LoopRun: {goal_id}")

        path = self.root_path / goal_record["path"]
        previous = path.read_text(encoding="utf-8")
        body = self._body_from_document(previous)
        goal_fm["status"] = status
        path.write_text(self._render_markdown(goal_fm, body), encoding="utf-8", newline="\n")
        try:
            self._require_conformant_bundle()
        except Exception:
            path.write_text(previous, encoding="utf-8", newline="\n")
            self._reload()
            raise

        self._reload()
        return {
            "id": goal_id,
            "run": run_id,
            "status": status,
            "check": self.check_run(run_id),
        }

    def record_run_decision(
        self,
        *,
        run: str,
        component_id: str,
        question: str,
        decision: str,
        rationale: str,
        goal: str | None = None,
        alternatives: list[str] | None = None,
        evidence: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record one consequential decision made during a live run."""
        return self._record_run_component(
            "RunDecision",
            run,
            component_id,
            {
                "question": question,
                "decision": decision,
                "rationale": rationale,
                "goal": goal,
                "alternatives": alternatives,
                "evidence": evidence,
            },
        )

    def record_run_evidence(
        self,
        *,
        run: str,
        component_id: str,
        kind: str,
        reference: str,
        summary: str,
        goal: str | None = None,
        decision: str | None = None,
        observed_at: str | None = None,
    ) -> dict[str, Any]:
        """Record one concrete item of evidence for a live run."""
        return self._record_run_component(
            "RunEvidence",
            run,
            component_id,
            {
                "kind": kind,
                "reference": reference,
                "summary": summary,
                "goal": goal,
                "decision": decision,
                "observed_at": observed_at,
            },
        )

    def record_run_check(
        self,
        *,
        run: str,
        component_id: str,
        kind: str,
        procedure: str,
        result: str,
        status: str,
        evidence: str | None = None,
        goal: str | None = None,
    ) -> dict[str, Any]:
        """Record one explicit verification performed during a live run."""
        self._require_enum("status", status, _CHECK_STATUSES)
        return self._record_run_component(
            "RunCheck",
            run,
            component_id,
            {
                "kind": kind,
                "procedure": procedure,
                "result": result,
                "status": status,
                "evidence": evidence,
                "goal": goal,
            },
        )

    def record_run_outcome(
        self,
        *,
        run: str,
        component_id: str,
        result_state: str,
        work_status: str,
        summary: str,
        next_move: str,
        goals_advanced: list[str] | None = None,
        evidence: list[str] | None = None,
        checks: list[str] | None = None,
        experiences_recorded: list[str] | None = None,
    ) -> dict[str, Any]:
        """Close one run round with its coherent state and natural continuation."""
        self._require_enum("work_status", work_status, _WORK_STATUSES)
        if work_status == "partial":
            run_record = self._find_record("LoopRun", run)
            run_id = str(run_record["frontmatter"].get("id") or run_record["id"])
            handoffs = [
                item
                for item in self._records("Handoff")
                if str(item["frontmatter"].get("created_by_run") or "") == run_id
            ]
            if not handoffs:
                msg = "Partial RunOutcome requires a Handoff before the LoopRun can close."
                raise ValueError(msg)
        return self._record_run_component(
            "RunOutcome",
            run,
            component_id,
            {
                "result_state": result_state,
                "work_status": work_status,
                "summary": summary,
                "next_move": next_move,
                "goals_advanced": goals_advanced,
                "evidence": evidence,
                "checks": checks,
                "experiences_recorded": experiences_recorded,
            },
        )

    def _record_run_component(
        self,
        concept_type: str,
        run_identifier: str,
        component_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        run = self._find_record("LoopRun", run_identifier)
        run_fm = dict(run["frontmatter"])
        run_id = str(run_fm.get("id") or run["id"])
        if str(run_fm.get("status") or "") == "closed":
            raise ValueError(f"LoopRun is already closed: {run_id}")

        prefix = _COMPONENT_PREFIXES[concept_type]
        field = _COMPONENT_FIELDS[concept_type]
        label = _COMPONENT_LABELS[concept_type]
        if field == "outcome":
            current = self.check_run(run_id)
            prerequisites = [
                item for item in current["unsatisfied"] if item.get("requirement") != "outcome"
            ]
            if prerequisites:
                pending = ", ".join(str(item.get("requirement")) for item in prerequisites)
                raise ValueError(f"LoopRun has unmet prerequisites before outcome: {pending}")

        slug = self._slug(component_id.rsplit("/", 1)[-1])
        if not slug:
            raise ValueError("component_id must contain a usable identifier")
        self._require_non_empty(fields)

        run_slug = self._slug(run_id.rsplit("/", 1)[-1])
        canonical_id = f"{prefix}/{run_slug}/{slug}"
        run_path = self.root_path / run["path"]
        component_path = run_path.parent / f"{run_slug}-{label}-{slug}.md"
        if component_path.exists():
            raise FileExistsError(component_path)
        if field == "outcome" and run_fm.get("outcome"):
            raise ValueError(f"LoopRun already has an outcome: {run_id}")

        frontmatter = {
            "type": concept_type,
            "id": canonical_id,
            "run": run_id,
            **{key: value for key, value in fields.items() if value is not None},
        }
        previous_run = run_path.read_text(encoding="utf-8")
        run_body = self._body_from_document(previous_run)
        updated_run = dict(run_fm)
        if field == "outcome":
            updated_run["outcome"] = canonical_id
            updated_run["status"] = "closed"
        else:
            links = [str(item) for item in updated_run.get(field, [])]
            if canonical_id not in links:
                links.append(canonical_id)
            updated_run[field] = links
            if str(updated_run.get("status") or "") == "scaffold":
                updated_run["status"] = "in_progress"

        component_content = self._render_markdown(frontmatter, f"# {concept_type}\n")
        run_content = self._render_markdown(updated_run, run_body)
        try:
            with component_path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(component_content)
            run_path.write_text(run_content, encoding="utf-8", newline="\n")
            self._require_conformant_bundle()
        except Exception:
            component_path.unlink(missing_ok=True)
            run_path.write_text(previous_run, encoding="utf-8", newline="\n")
            self._reload()
            raise

        self._reload()
        return {
            "id": canonical_id,
            "path": str(component_path),
            "run": run_id,
            "run_status": str(updated_run["status"]),
            "check": self.check_run(run_id),
        }

    @staticmethod
    def _require_non_empty(fields: dict[str, Any]) -> None:
        for key, value in fields.items():
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"{key} must not be empty")

    @staticmethod
    def _require_enum(name: str, value: str, allowed: frozenset[str]) -> None:
        if value not in allowed:
            choices = ", ".join(sorted(allowed))
            raise ValueError(f"{name} must be one of: {choices}")
