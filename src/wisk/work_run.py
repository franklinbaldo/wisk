"""RFC 0007 Work-trace runtime: raw observations, skill provenance, and role-aware context."""

from __future__ import annotations

import math
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from okf_parser import load_bundle

from wisk.live_run import LiveRunWisk

_OBSERVATION_IMPACTS = frozenset({"low", "medium", "high"})
_SKILL_USE_STATUSES = frozenset({"active", "experimental"})
_SCHEDULER_COMPATIBILITY_ALIASES = frozenset(
    {
        "session-types/experience",
        "session-types/standard-experience",
        "session-types/inference",
    }
)
_DEPRECATED_EXECUTION_IDS = frozenset(
    {
        "session-types/experience",
        "session-types/standard-experience",
    }
)


class WorkRunWisk(LiveRunWisk):
    """Live runtime whose Work LoopRuns are the canonical repository Raw Layer."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> WorkRunWisk:
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def start_run(
        self,
        task: str,
        run_spec_id: str | None = None,
        session_type_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a run and persist explicit lifecycle start provenance."""
        result = super().start_run(task, run_spec_id, session_type_id)
        run = self._find_record("LoopRun", result["run_id"])
        path = self.root_path / run["path"]
        previous = path.read_text(encoding="utf-8")
        frontmatter = dict(run["frontmatter"])
        started_at = str(
            frontmatter.get("started_at") or frontmatter.get("timestamp") or self._now()
        )
        frontmatter["started_at"] = started_at
        # Keep timestamp during the 0.4 RC migration window so 0.3.x consumers remain readable.
        frontmatter.setdefault("timestamp", started_at)
        body = self._body_from_document(previous)
        path.write_text(self._render_markdown(frontmatter, body), encoding="utf-8", newline="\n")
        try:
            self._require_conformant_bundle()
        except Exception:
            path.write_text(previous, encoding="utf-8", newline="\n")
            self._reload()
            raise
        self._reload()
        result["started_at"] = started_at
        result["check"] = self.check_run(result["run_id"])
        return result

    def record_run_observation(
        self,
        *,
        run: str,
        component_id: str,
        kind: str,
        summary: str,
        impact: str,
        observed_at: str | None = None,
        skill_use: str | None = None,
    ) -> dict[str, Any]:
        """Record raw execution texture without prematurely turning it into Wiki knowledge."""
        self._require_enum("impact", impact, _OBSERVATION_IMPACTS)
        return self._record_raw_component(
            concept_type="RunObservation",
            run_identifier=run,
            component_id=component_id,
            prefix="run-observations",
            label="observation",
            fields={
                "kind": kind,
                "summary": summary,
                "impact": impact,
                "observed_at": observed_at or self._now(),
                "skill_use": skill_use,
            },
        )

    def record_run_skill_use(
        self,
        *,
        run: str,
        component_id: str,
        skill: str,
        skill_version: str,
        skill_status: str,
        observed_at: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Record the exact executable skill/version that actually guided one Work run."""
        self._require_enum("skill_status", skill_status, _SKILL_USE_STATUSES)
        skill_record = self._find_record("AgentSkill", skill)
        skill_fm = skill_record["frontmatter"]
        canonical_skill = str(skill_fm.get("id") or skill_record["id"])
        actual_version = str(skill_fm.get("version") or "")
        actual_status = str(skill_fm.get("status") or "")
        if actual_version and actual_version != skill_version:
            raise ValueError(
                f"skill_version does not match AgentSkill {canonical_skill}: "
                f"expected {actual_version}, got {skill_version}"
            )
        if actual_status in _SKILL_USE_STATUSES and actual_status != skill_status:
            raise ValueError(
                f"skill_status does not match AgentSkill {canonical_skill}: "
                f"expected {actual_status}, got {skill_status}"
            )
        return self._record_raw_component(
            concept_type="RunSkillUse",
            run_identifier=run,
            component_id=component_id,
            prefix="run-skill-uses",
            label="skill-use",
            fields={
                "skill": canonical_skill,
                "skill_version": skill_version,
                "skill_status": skill_status,
                "observed_at": observed_at or self._now(),
                "notes": notes,
            },
        )

    def record_run_outcome(self, **kwargs: Any) -> dict[str, Any]:
        """Close a run and persist its objective finish timestamp."""
        result = super().record_run_outcome(**kwargs)
        run_identifier = str(kwargs["run"])
        run = self._find_record("LoopRun", run_identifier)
        path = self.root_path / run["path"]
        previous = path.read_text(encoding="utf-8")
        frontmatter = dict(run["frontmatter"])
        finished_at = str(frontmatter.get("finished_at") or self._now())
        frontmatter["finished_at"] = finished_at
        body = self._body_from_document(previous)
        path.write_text(self._render_markdown(frontmatter, body), encoding="utf-8", newline="\n")
        try:
            self._require_conformant_bundle()
        except Exception:
            path.write_text(previous, encoding="utf-8", newline="\n")
            self._reload()
            raise
        self._reload()
        result["finished_at"] = finished_at
        duration = self._duration_seconds(frontmatter)
        if duration is not None:
            result["duration_seconds"] = duration
        result["check"] = self.check_run(str(frontmatter.get("id") or run["id"]))
        return result

    def run_trace(self, run: str) -> dict[str, Any]:
        """Reconstruct a Work trace through okf-parser's declared typed relations."""
        record = self._find_record("LoopRun", run)
        frontmatter = dict(record["frontmatter"])
        run_id = str(frontmatter.get("id") or record["id"])
        components = self._typed_trace_components(self._trace_mapping(), run_id)
        return {
            "id": run_id,
            "path": record["path"],
            "run": frontmatter,
            "duration_seconds": self._duration_seconds(frontmatter),
            **components,
        }

    def _trace_mapping(self) -> dict[str, str]:
        """Return Raw Layer child collections materialized in one typed trace snapshot."""
        return {
            "readings": "RunReading",
            "goals": "RunGoal",
            "decisions": "RunDecision",
            "evidence": "RunEvidence",
            "checks": "RunCheck",
            "observations": "RunObservation",
            "skill_uses": "RunSkillUse",
            "outcomes": "RunOutcome",
        }

    def _typed_trace_components(
        self,
        mapping: dict[str, str],
        run_id: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """Read declared Run* values through okf-parser instead of raw YAML strings."""
        bundle = self._reload()
        result: dict[str, list[dict[str, Any]]] = {}
        with bundle.compile_types("../specs/{slug}.md") as typed:
            for name, concept_type in mapping.items():
                if concept_type not in typed.tables:
                    result[name] = [
                        dict(item["frontmatter"])
                        for item in self._run_components(concept_type, run_id)
                    ]
                    continue
                relation = typed[concept_type]
                if "run" not in relation.columns:
                    result[name] = []
                    continue
                frame = relation.filter(relation["run"] == run_id).execute()
                records: list[dict[str, Any]] = []
                for _, row in frame.iterrows():
                    frontmatter: dict[str, Any] = {}
                    for column in frame.columns:
                        key = str(column)
                        if key.startswith("__okf_"):
                            continue
                        value = self._runtime_value(row[column])
                        if value is not None:
                            frontmatter[key] = value
                    records.append(frontmatter)
                result[name] = records
        return result

    @classmethod
    def _runtime_value(cls, value: Any) -> Any:
        """Keep parser types while making temporal/scalar values JSON-boundary friendly."""
        if value is None or type(value).__name__ in {"NAType", "NaTType"}:
            return None
        if isinstance(value, datetime):
            return value.isoformat().replace("+00:00", "Z")
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, float) and math.isnan(value):
            return None
        if isinstance(value, list):
            return [cls._runtime_value(item) for item in value]
        if isinstance(value, tuple):
            return [cls._runtime_value(item) for item in value]
        item = getattr(value, "item", None)
        if callable(item):
            try:
                return cls._runtime_value(item())
            except (TypeError, ValueError):
                pass
        return value

    def check_run(self, run_id_or_path: str) -> dict[str, Any]:
        """Preserve RunSpec semantics while exposing the complete Raw Layer component counts."""
        result = super().check_run(run_id_or_path)
        run = self._find_record("LoopRun", run_id_or_path)
        run_id = str(run["frontmatter"].get("id") or run["id"])
        counts = dict(result.get("counts") or {})
        counts["observations"] = len(self._run_components("RunObservation", run_id))
        counts["skill_uses"] = len(self._run_components("RunSkillUse", run_id))
        result["counts"] = counts
        return result

    def context(self, task: str, session_type_id: str | None = None) -> dict[str, Any]:
        """Add Work corpus and proposal-history surfaces to role-curated context."""
        result = super().context(task, session_type_id)
        policy = result.get("context_policy") or {}
        include = {str(item) for item in policy.get("include", [])}
        exclude = {str(item) for item in policy.get("exclude", [])}
        curated = str(policy.get("mode") or "advisory") == "curated"

        work_runs = self._work_run_context_records()
        proposals = self._context_records("SkillProposal")
        if curated and ("work-runs" in exclude or (include and "work-runs" not in include)):
            work_runs = []
        if curated and ("proposals" in exclude or (include and "proposals" not in include)):
            proposals = []
        result["recent_work_runs"] = work_runs[:20]
        result["skill_proposals"] = proposals
        return result

    def start(
        self,
        task: str | None = None,
        *,
        session_type: str | None = None,
        run_spec: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        result = super().start(task, session_type=session_type, run_spec=run_spec, now=now)
        if session_type in _DEPRECATED_EXECUTION_IDS:
            result["deprecation"] = (
                f"{session_type} is a 0.4 RC compatibility alias; use session-types/work "
                "or a Work specialization for new sessions."
            )
        return result

    def _scheduler_session_types(self) -> list[dict[str, Any]]:
        """Do not auto-select exact pre-0.4 aliases; consumer children remain eligible."""
        return [
            item
            for item in super()._scheduler_session_types()
            if str(item.get("id") or "") not in _SCHEDULER_COMPATIBILITY_ALIASES
        ]

    def _metric_value(
        self,
        metric: str,
        session_type_id: str,
        last_run: datetime | None,
    ) -> int | None:
        if metric == "work-runs-since-last-run":
            return sum(
                1
                for item in self._closed_work_runs()
                if last_run is None
                or (stamp := self._timestamp(item)) is not None
                and stamp > last_run
            )
        return super()._metric_value(metric, session_type_id, last_run)

    def _closed_work_runs(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for run in self._records("LoopRun"):
            fm = run["frontmatter"]
            if str(fm.get("status") or "") != "closed":
                continue
            session_id = str(fm.get("session_type") or "")
            if not session_id:
                continue
            try:
                session = self.effective_session_type(session_id)
            except ValueError:
                continue
            lineage = {str(item) for item in session.get("inheritance", [])}
            lineage.add(str(session.get("id") or ""))
            if "session-types/work" in lineage:
                result.append(run)
        return result

    def _work_run_context_records(self) -> list[dict[str, Any]]:
        records = sorted(
            self._closed_work_runs(),
            key=lambda item: self._timestamp(item) or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        result: list[dict[str, Any]] = []
        for item in records:
            fm = item["frontmatter"]
            result.append(
                {
                    "id": str(fm.get("id") or item["id"]),
                    "type": "LoopRun",
                    "title": item["title"],
                    "path": item["path"],
                    "session_type": str(fm.get("session_type") or ""),
                    "task": str(fm.get("task") or ""),
                    "started_at": fm.get("started_at") or fm.get("timestamp"),
                    "finished_at": fm.get("finished_at"),
                }
            )
        return result

    def _record_raw_component(
        self,
        *,
        concept_type: str,
        run_identifier: str,
        component_id: str,
        prefix: str,
        label: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        run = self._find_record("LoopRun", run_identifier)
        run_fm = dict(run["frontmatter"])
        run_id = str(run_fm.get("id") or run["id"])
        if str(run_fm.get("status") or "") == "closed":
            raise ValueError(f"LoopRun is already closed: {run_id}")

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

        frontmatter = {
            "type": concept_type,
            "id": canonical_id,
            "run": run_id,
            **{key: value for key, value in fields.items() if value is not None},
        }
        previous_run = run_path.read_text(encoding="utf-8")
        run_body = self._body_from_document(previous_run)
        updated_run = dict(run_fm)
        if str(updated_run.get("status") or "") == "scaffold":
            updated_run["status"] = "in_progress"

        try:
            with component_path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(self._render_markdown(frontmatter, f"# {concept_type}\n"))
            run_path.write_text(
                self._render_markdown(updated_run, run_body),
                encoding="utf-8",
                newline="\n",
            )
            self._require_conformant_bundle()
        except Exception:
            component_path.unlink(missing_ok=True)
            run_path.write_text(previous_run, encoding="utf-8", newline="\n")
            self._reload()
            raise

        self._reload()
        return self._progress_result(
            run_id,
            {
                "id": canonical_id,
                "path": str(component_path),
                "run_status": str(updated_run["status"]),
            },
        )

    @staticmethod
    def _duration_seconds(frontmatter: dict[str, Any]) -> float | None:
        started = str(frontmatter.get("started_at") or frontmatter.get("timestamp") or "")
        finished = str(frontmatter.get("finished_at") or "")
        if not started or not finished:
            return None
        try:
            start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            finish_dt = datetime.fromisoformat(finished.replace("Z", "+00:00"))
        except ValueError:
            return None
        return max(0.0, (finish_dt - start_dt).total_seconds())

    @staticmethod
    def _timestamp(record: dict[str, Any]) -> datetime | None:
        frontmatter = record["frontmatter"]
        value = str(
            frontmatter.get("finished_at")
            or frontmatter.get("started_at")
            or frontmatter.get("timestamp")
            or frontmatter.get("created_at")
            or ""
        )
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None
