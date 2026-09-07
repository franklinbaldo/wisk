"""Declarative eligibility and scheduling for Wisk SessionTypes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from okf_parser import load_bundle

from wisk.policy import PolicyWisk

_DEFAULT_TASK = "Do the best useful work available in this repository."
_LIVE_STATUSES = frozenset({"scaffold", "active", "in_progress"})


class CadenceWisk(PolicyWisk):
    """Policy-aware runtime that can explain and select eligible sessions."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> CadenceWisk:
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    def effective_session_type(self, identifier: str) -> dict[str, Any]:
        session = super().effective_session_type(identifier)
        cadence_ref = str(session.get("cadence_policy") or "")
        session["cadence"] = self._cadence_policy(cadence_ref) if cadence_ref else None
        return session

    def _cadence_policy(self, identifier: str) -> dict[str, Any]:
        record = self._find_record("CadencePolicy", identifier)
        result = dict(record["frontmatter"])
        result["id"] = str(result.get("id") or record["id"])
        result["path"] = record["path"]
        return result

    def session_eligibility(
        self,
        session_type_id: str,
        *,
        now: datetime | None = None,
        requested: bool = False,
    ) -> dict[str, Any]:
        """Explain whether a SessionType is eligible at this instant."""
        current = (now or datetime.now(UTC)).astimezone(UTC)
        session = self.effective_session_type(session_type_id)
        cadence = session.get("cadence")
        if not cadence:
            return {
                "session_type": session["id"],
                "eligible": requested,
                "priority": 0,
                "reasons": ["explicit-request"] if requested else [],
                "blockers": [] if requested else ["no-cadence-policy"],
                "metrics": {},
            }

        runs = self._session_runs(session["id"])
        last_run = self._latest_timestamp(runs)
        active_runs = sum(
            1 for run in runs if str(run["frontmatter"].get("status") or "") in _LIVE_STATUSES
        )
        runs_last_hour = sum(
            1
            for run in runs
            if (stamp := self._timestamp(run)) is not None and current - stamp <= timedelta(hours=1)
        )
        lineage = set(str(item) for item in session.get("inheritance", []))
        lineage.add(str(session["id"]))
        matching_handoffs = [
            item
            for item in self.active_handoffs()
            if not item.get("target_session_type")
            or str(item.get("target_session_type") or "") in lineage
        ]
        threshold_value = self._metric_value(
            str(cadence.get("threshold_metric") or ""),
            session["id"],
            last_run,
        )

        reasons: list[str] = []
        blockers: list[str] = []
        if requested and self._bool(cadence.get("on_demand")):
            reasons.append("explicit-request")
        if matching_handoffs and self._bool(cadence.get("handoff_compatible")):
            reasons.append("active-handoff")

        interval = self._int(cadence.get("interval_seconds"))
        if interval and (last_run is None or (current - last_run).total_seconds() >= interval):
            reasons.append("interval")

        threshold_gte = self._int(cadence.get("threshold_gte"))
        threshold_reached = (
            threshold_gte is not None
            and threshold_value is not None
            and threshold_value >= threshold_gte
        )
        if threshold_reached:
            reasons.append("threshold")

        max_delay = self._int(cadence.get("max_delay_seconds"))
        if max_delay and (last_run is None or (current - last_run).total_seconds() >= max_delay):
            reasons.append("max-delay")

        cooldown = self._int(cadence.get("cooldown_seconds"))
        if cooldown and last_run is not None and (current - last_run).total_seconds() < cooldown:
            blockers.append("cooldown")

        max_parallel = self._int(cadence.get("max_parallel"))
        if max_parallel is not None and active_runs >= max_parallel:
            blockers.append("max-parallel")

        max_runs_per_hour = self._int(cadence.get("max_runs_per_hour"))
        if max_runs_per_hour is not None and runs_last_hour >= max_runs_per_hour:
            blockers.append("hourly-budget")

        return {
            "session_type": session["id"],
            "eligible": bool(reasons) and not blockers,
            "priority": self._int(cadence.get("priority")) or 0,
            "reasons": reasons,
            "blockers": blockers,
            "metrics": {
                "active_runs": active_runs,
                "runs_last_hour": runs_last_hour,
                "threshold_value": threshold_value,
                "targeted_handoffs": len(matching_handoffs),
                "last_run": last_run.isoformat().replace("+00:00", "Z") if last_run else None,
            },
        }

    def _scheduler_session_types(self) -> list[dict[str, Any]]:
        """Return only leaf SessionTypes for automatic/requested selection."""
        records = self._records("SessionType")
        extended = {
            str(item["frontmatter"].get("extends") or "")
            for item in records
            if item["frontmatter"].get("extends")
        }
        leaves: list[dict[str, Any]] = []
        for item in records:
            canonical_id = str(item["frontmatter"].get("id") or item["id"])
            if canonical_id in extended or canonical_id == "session-types/base":
                continue
            leaves.append(self.effective_session_type(canonical_id))
        return leaves

    def eligible_sessions(
        self,
        *,
        now: datetime | None = None,
        requested: bool = False,
    ) -> list[dict[str, Any]]:
        """Return eligible leaf sessions ordered deterministically."""
        candidates = [
            self.session_eligibility(item["id"], now=now, requested=requested)
            for item in self._scheduler_session_types()
        ]
        eligible = [item for item in candidates if item["eligible"]]
        return sorted(eligible, key=lambda item: (-item["priority"], item["session_type"]))

    def next_session(
        self,
        *,
        now: datetime | None = None,
        requested: bool = False,
    ) -> dict[str, Any] | None:
        """Return the highest-priority eligible SessionType."""
        eligible = self.eligible_sessions(now=now, requested=requested)
        return eligible[0] if eligible else None

    def start(
        self,
        task: str | None = None,
        *,
        session_type: str | None = None,
        run_spec: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Start or resume the golden-path LoopRun and return one stable state envelope."""
        effective_task = task.strip() if task and task.strip() else _DEFAULT_TASK
        resumed = self._resume_candidate(task=task, session_type_id=session_type)
        if resumed is not None:
            check = self.check_run(resumed["id"])
            return self._operation_envelope(
                check,
                selection_reason="active-run-resume",
                resumed=True,
            )

        if session_type:
            eligibility = self.session_eligibility(session_type, now=now, requested=False)
            blockers = [item for item in eligibility["blockers"] if item != "no-cadence-policy"]
            if blockers:
                return {
                    "run": None,
                    "state": "blocked",
                    "session_type": eligibility["session_type"],
                    "selection_reason": "explicit-override",
                    "blockers": blockers,
                    "remediation": self._remediation(blockers),
                }
            selected = {
                **eligibility,
                "eligible": True,
                "reasons": ["explicit-override"],
            }
            selection_reason = "explicit-override"
        else:
            selected = self.next_session(now=now, requested=True)
            if selected is None:
                candidates = [
                    self.session_eligibility(item["id"], now=now, requested=True)
                    for item in self._scheduler_session_types()
                ]
                blockers = sorted({b for item in candidates for b in item["blockers"]})
                return {
                    "run": None,
                    "state": "blocked",
                    "session_type": None,
                    "selection_reason": None,
                    "blockers": blockers or ["no-eligible-session"],
                    "remediation": self._remediation(blockers or ["no-eligible-session"]),
                    "candidates": candidates,
                }
            reasons = list(selected.get("reasons", []))
            if "active-handoff" in reasons:
                selection_reason = "handoff-continuation"
            elif "explicit-request" in reasons:
                selection_reason = "on-demand-fallback"
            else:
                selection_reason = reasons[0] if reasons else "cadence"

        result = self.start_run(
            effective_task,
            run_spec_id=run_spec,
            session_type_id=str(selected["session_type"]),
        )
        check = result.get("check") or self.check_run(result["run_id"])
        envelope = self._operation_envelope(
            check,
            selection_reason=selection_reason,
            resumed=False,
        )
        envelope["effective_task"] = effective_task
        envelope["run_spec"] = result.get("run_spec")
        envelope["session_type"] = result.get("session_type") or selected["session_type"]
        return envelope

    def start_next_session(
        self,
        task: str,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Compatibility alias for the pre-RFC explicit requested start."""
        candidate = self.next_session(now=now, requested=True)
        if candidate is None:
            raise ValueError("No SessionType is currently eligible for requested start.")
        return self.start_run(task, session_type_id=candidate["session_type"])

    def _resume_candidate(
        self,
        *,
        task: str | None,
        session_type_id: str | None,
    ) -> dict[str, Any] | None:
        live = [
            run
            for run in self._records("LoopRun")
            if str(run["frontmatter"].get("status") or "") in _LIVE_STATUSES
        ]
        if session_type_id:
            requested = self.effective_session_type(session_type_id)["id"]
            live = [
                run
                for run in live
                if str(run["frontmatter"].get("session_type") or "") == requested
            ]
        if task and task.strip():
            live = [
                run
                for run in live
                if str(run["frontmatter"].get("task") or "").strip() == task.strip()
            ]
        if not live:
            return None

        def rank(run: dict[str, Any]) -> tuple[int, datetime, str]:
            session_id = str(run["frontmatter"].get("session_type") or "")
            try:
                session = self.effective_session_type(session_id)
                cadence = session.get("cadence") or {}
                priority = self._int(cadence.get("priority")) or 0
            except ValueError:
                priority = 0
            stamp = self._timestamp(run) or datetime.min.replace(tzinfo=UTC)
            return (-priority, stamp, str(run["id"]))

        return sorted(live, key=rank)[0]

    def _operation_envelope(
        self,
        check: dict[str, Any],
        *,
        selection_reason: str,
        resumed: bool,
    ) -> dict[str, Any]:
        next_action = dict(check.get("next_action") or {})
        run_id = str(check.get("run_id") or "") or None
        session_type = check.get("session_type")
        if run_id and not session_type:
            try:
                run = self._find_record("LoopRun", run_id)
                session_type = run["frontmatter"].get("session_type")
            except ValueError:
                session_type = None
        if check.get("conformant") or next_action.get("kind") == "complete":
            state = "done"
            payload: dict[str, Any] = {}
        elif next_action.get("kind") == "blocked":
            state = "blocked"
            payload = {
                "blockers": list(next_action.get("blockers", [])),
                "remediation": list(next_action.get("remediation", [])),
            }
        else:
            state = "next"
            payload = {"next": next_action}
        return {
            "run": run_id,
            "state": state,
            "selection_reason": selection_reason,
            "resumed": resumed,
            "session_type": session_type,
            "run_spec": check.get("run_spec"),
            **payload,
        }

    @staticmethod
    def _remediation(blockers: list[str]) -> list[dict[str, str]]:
        actions: list[dict[str, str]] = []
        for blocker in blockers:
            if blocker in {"cooldown", "hourly-budget"}:
                actions.append({"action": "retry_later", "reason": blocker})
            elif blocker == "max-parallel":
                actions.append({"action": "resume_active_run", "reason": blocker})
            elif blocker == "no-eligible-session":
                actions.append({"action": "inspect_session_status", "reason": blocker})
            else:
                actions.append({"action": "inspect_blocker", "reason": blocker})
        return actions

    def _session_runs(self, session_type_id: str) -> list[dict[str, Any]]:
        return [
            run
            for run in self._records("LoopRun")
            if str(run["frontmatter"].get("session_type") or "") == session_type_id
        ]

    def _metric_value(
        self,
        metric: str,
        session_type_id: str,
        last_run: datetime | None,
    ) -> int | None:
        if not metric:
            return None
        if metric == "experiences-since-last-run":
            return sum(
                1
                for item in self._records("Experience")
                if last_run is None
                or (stamp := self._timestamp(item)) is not None
                and stamp > last_run
            )
        if metric == "active-handoffs":
            session = self.effective_session_type(session_type_id)
            lineage = set(str(item) for item in session.get("inheritance", []))
            lineage.add(str(session["id"]))
            return sum(
                1
                for item in self.active_handoffs()
                if not item.get("target_session_type")
                or str(item.get("target_session_type") or "") in lineage
            )
        raise ValueError(f"Unknown cadence threshold metric: {metric}")

    def _latest_timestamp(self, records: list[dict[str, Any]]) -> datetime | None:
        stamps = [stamp for item in records if (stamp := self._timestamp(item)) is not None]
        return max(stamps) if stamps else None

    @staticmethod
    def _timestamp(record: dict[str, Any]) -> datetime | None:
        frontmatter = record["frontmatter"]
        value = str(frontmatter.get("timestamp") or frontmatter.get("created_at") or "")
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None

    @staticmethod
    def _int(value: Any) -> int | None:
        if value is None or value == "":
            return None
        return int(value)

    @staticmethod
    def _bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "yes", "1", "on"}:
                return True
            if normalized in {"false", "no", "0", "off", ""}:
                return False
        return bool(value)