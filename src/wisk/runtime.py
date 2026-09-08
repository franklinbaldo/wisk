"""Core Wisk runtime facade."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from okf_parser import Bundle, load_bundle
from okf_parser.service import check_bundle

_EXPERIENCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_EXPERIENCE_STATUSES = frozenset({"success", "failure", "partial", "observation"})


class Wisk:
    """Contract-guided agent execution and learning runtime backed by OKF."""

    def __init__(self, bundle: Bundle, root_path: Path) -> None:
        self.bundle = bundle
        self.root_path = root_path

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> Wisk:
        """Open an existing OKF knowledge bundle."""
        root = Path(path).resolve()
        bundle = load_bundle(root)
        return cls(bundle=bundle, root_path=root)

    def _reload(self) -> Bundle:
        self.bundle = load_bundle(self.root_path)
        return self.bundle

    def _records(self, concept_type: str) -> list[dict[str, Any]]:
        frame = self._reload().concepts.execute()
        records: list[dict[str, Any]] = []
        for _, row in frame.iterrows():
            if str(row["concept_type"]) != concept_type:
                continue
            raw = str(row.get("frontmatter_json") or "{}")
            frontmatter = json.loads(raw)
            records.append(
                {
                    "id": str(row["concept_id"]),
                    "path": str(row.get("path") or ""),
                    "title": str(row.get("title") or frontmatter.get("title") or ""),
                    "frontmatter": frontmatter,
                }
            )
        return records

    def inventory(self) -> dict[str, int]:
        """Return counts of concepts grouped by concept_type."""
        df = (
            self.bundle.concepts.group_by("concept_type")
            .aggregate(count=self.bundle.concepts.count())
            .execute()
        )
        return dict(zip(df["concept_type"], df["count"], strict=True))

    def preview_experience(
        self,
        *,
        experience_id: str,
        title: str,
        timestamp: str,
        status: str,
        body: str,
        skill_used: str | None = None,
        skill_version: str | None = None,
        task: str | None = None,
        error_code: str | None = None,
        context: str | None = None,
        run: str | None = None,
    ) -> dict[str, str]:
        """Render one Experience without mutating the knowledge bundle."""
        if not _EXPERIENCE_ID_RE.fullmatch(experience_id):
            msg = "experience_id must be a filename-safe identifier"
            raise ValueError(msg)
        if status not in _EXPERIENCE_STATUSES:
            allowed = ", ".join(sorted(_EXPERIENCE_STATUSES))
            msg = f"status must be one of: {allowed}"
            raise ValueError(msg)
        if not title.strip():
            raise ValueError("title must not be empty")
        if not timestamp.strip():
            raise ValueError("timestamp must not be empty")
        if not body.strip():
            raise ValueError("body must not be empty")

        relative_path = Path("experiences") / f"{experience_id}.md"
        if (self.root_path / relative_path).exists():
            raise FileExistsError(self.root_path / relative_path)

        frontmatter: dict[str, Any] = {
            "type": "Experience",
            "id": experience_id,
            "title": title,
            "timestamp": timestamp,
            "status": status,
        }
        optional_fields = {
            "skill_used": skill_used,
            "skill_version": skill_version,
            "task": task,
            "error_code": error_code,
            "context": context,
            "run": run,
        }
        frontmatter.update(
            {key: value for key, value in optional_fields.items() if value is not None}
        )
        content = self._render_markdown(frontmatter, body)
        return {
            "id": experience_id,
            "path": relative_path.as_posix(),
            "content": content,
        }

    def record_experience(
        self,
        *,
        experience_id: str,
        title: str,
        timestamp: str,
        status: str,
        body: str,
        skill_used: str | None = None,
        skill_version: str | None = None,
        task: str | None = None,
        error_code: str | None = None,
        context: str | None = None,
        run: str | None = None,
    ) -> dict[str, str | bool]:
        """Persist one Experience and roll back if normative OKF validation fails."""
        preview = self.preview_experience(
            experience_id=experience_id,
            title=title,
            timestamp=timestamp,
            status=status,
            body=body,
            skill_used=skill_used,
            skill_version=skill_version,
            task=task,
            error_code=error_code,
            context=context,
            run=run,
        )
        target = self.root_path / preview["path"]
        target.parent.mkdir(parents=True, exist_ok=True)

        try:
            with target.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(preview["content"])
            report = check_bundle(
                str(self.root_path),
                require_spec="../specs/{slug}.md",
                normative_spec=True,
            )
            if not bool(report["conformant"]):
                diagnostics = report.get("diagnostics", [])
                msg = f"Experience write would make the OKF bundle invalid: {diagnostics!r}"
                raise ValueError(msg)
            self._reload()
        except Exception:
            target.unlink(missing_ok=True)
            self._reload()
            raise

        return {
            "id": experience_id,
            "path": preview["path"],
            "written": True,
        }

    def context(self, task: str) -> dict[str, Any]:
        """Extract execution contracts and learned context relevant to a task."""
        keywords = [k.lower() for k in task.split() if len(k) > 2]

        concepts_df = self.bundle.concepts.execute()
        relevant_run_specs: list[dict[str, Any]] = []
        relevant_skills: list[dict[str, Any]] = []
        relevant_wiki: list[dict[str, Any]] = []
        recent_experiences: list[dict[str, Any]] = []

        for _, row in concepts_df.iterrows():
            ctype = row["concept_type"]
            title = str(row.get("title") or "")
            cid = str(row["concept_id"])
            text_corpus = f"{cid} {title}".lower()
            matched = any(k in text_corpus for k in keywords) if keywords else True

            record = {
                "id": cid,
                "type": ctype,
                "title": title,
                "path": str(row.get("path") or ""),
            }

            if ctype == "RunSpec" and matched:
                relevant_run_specs.append(record)
            elif ctype == "AgentSkill" and matched:
                relevant_skills.append(record)
            elif ctype == "WikiEntry" and matched:
                relevant_wiki.append(record)
            elif ctype == "Experience":
                recent_experiences.append(record)

        return {
            "task": task,
            "run_specs": relevant_run_specs,
            "skills": relevant_skills,
            "wiki": relevant_wiki,
            "recent_experiences": recent_experiences[:5],
        }

    def start_run(self, task: str, run_spec_id: str | None = None) -> dict[str, Any]:
        """Create an intentionally incomplete LoopRun scaffold for a task."""
        spec = self._select_run_spec(task, run_spec_id)
        now = datetime.now(UTC)
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        slug = self._slug(task) or "run"
        run_id = f"runs/{stamp}-{slug}"
        run_dir = self.root_path / "runs"
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / f"{stamp}-{slug}.md"
        suffix = 2
        while path.exists():
            path = run_dir / f"{stamp}-{slug}-{suffix}.md"
            run_id = f"runs/{stamp}-{slug}-{suffix}"
            suffix += 1

        title = task.strip().splitlines()[0][:100] or "Agent run"
        frontmatter = {
            "type": "LoopRun",
            "id": run_id,
            "title": title,
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "status": "scaffold",
            "run_spec": spec["id"],
            "task": task,
        }
        path.write_text(self._render_markdown(frontmatter, "# Live run\n"), encoding="utf-8")
        self._reload()
        return {
            "run_id": run_id,
            "path": str(path),
            "run_spec": spec["id"],
            "status": "scaffold",
            "check": self.check_run(run_id),
        }

    def check_run(self, run_id_or_path: str) -> dict[str, Any]:
        """Return structural diagnostics, unmet requirements, and the next typed action."""
        structural = check_bundle(
            str(self.root_path),
            require_spec="../specs/{slug}.md",
            normative_spec=True,
        )
        run = self._find_record("LoopRun", run_id_or_path)
        run_fm = run["frontmatter"]
        spec_ref = str(run_fm.get("run_spec") or "")
        spec = self._find_record("RunSpec", spec_ref)
        spec_fm = spec["frontmatter"]
        run_id = str(run_fm.get("id") or run["id"])

        components = {
            "readings": self._run_components("RunReading", run_id),
            "goals": self._run_components("RunGoal", run_id),
            "decisions": self._run_components("RunDecision", run_id),
            "evidence": self._run_components("RunEvidence", run_id),
            "checks": self._run_components("RunCheck", run_id),
            "outcomes": self._run_components("RunOutcome", run_id),
        }

        unsatisfied: list[dict[str, Any]] = []
        requirements = (
            ("reading", "required_reading_kinds", components["readings"]),
            ("goal", "required_goal_kinds", components["goals"]),
            ("evidence", "required_evidence_kinds", components["evidence"]),
            ("check", "required_check_kinds", components["checks"]),
        )
        for label, field, records in requirements:
            required = [str(item) for item in spec_fm.get(field, [])]
            present = {str(item["frontmatter"].get("kind") or "") for item in records}
            for kind in required:
                if kind not in present:
                    unsatisfied.append(
                        {
                            "requirement": f"{label}:{kind}",
                            "kind": label,
                            "expected": kind,
                            "message": f"Record Run{label.title()} kind '{kind}'.",
                        }
                    )

        outcomes = components["outcomes"]
        if not outcomes:
            unsatisfied.append(
                {
                    "requirement": "outcome",
                    "kind": "outcome",
                    "message": "Record a RunOutcome for the state reached in this round.",
                }
            )
        else:
            allowed = {str(item) for item in spec_fm.get("allowed_result_states", [])}
            result_state = str(outcomes[-1]["frontmatter"].get("result_state") or "")
            if allowed and result_state not in allowed:
                unsatisfied.append(
                    {
                        "requirement": "outcome:result_state",
                        "kind": "outcome",
                        "expected": sorted(allowed),
                        "observed": result_state,
                        "message": "RunOutcome result_state is outside the governing RunSpec.",
                    }
                )

        conformant = bool(structural["conformant"]) and not unsatisfied
        if unsatisfied:
            next_action = dict(unsatisfied[0])
        elif conformant:
            next_action = {
                "kind": "complete",
                "requirement": None,
                "message": "Run satisfies its RunSpec.",
            }
        else:
            next_action = {
                "kind": "structural",
                "requirement": "okf",
                "message": "Resolve structural OKF diagnostics before continuing.",
            }

        return {
            "run_id": run_id,
            "run_spec": spec["id"],
            "conformant": conformant,
            "structural": structural,
            "unsatisfied": unsatisfied,
            "next_action": next_action,
            "counts": {name: len(records) for name, records in components.items()},
        }

    def _select_run_spec(self, task: str, requested: str | None) -> dict[str, Any]:
        specs = self._records("RunSpec")
        if not specs:
            msg = "No RunSpec concepts are available in the knowledge bundle."
            raise ValueError(msg)
        if requested is not None:
            for spec in specs:
                fm_id = str(spec["frontmatter"].get("id") or "")
                if requested in {spec["id"], fm_id, spec["path"]}:
                    return spec
            msg = f"RunSpec not found: {requested}"
            raise ValueError(msg)

        keywords = {word for word in re.findall(r"[a-z0-9_-]+", task.lower()) if len(word) > 2}

        def score(spec: dict[str, Any]) -> tuple[int, str]:
            fm = spec["frontmatter"]
            corpus = " ".join(
                [spec["id"], spec["title"], str(fm.get("id") or ""), str(fm.get("title") or "")]
            ).lower()
            matches = sum(1 for word in keywords if word in corpus)
            active = 1 if str(fm.get("status") or "") == "active" else 0
            return (matches * 10 + active, spec["id"])

        return max(specs, key=score)

    def _find_record(self, concept_type: str, identifier: str) -> dict[str, Any]:
        for record in self._records(concept_type):
            fm_id = str(record["frontmatter"].get("id") or "")
            if identifier in {record["id"], fm_id, record["path"]}:
                return record
        msg = f"{concept_type} not found: {identifier}"
        raise ValueError(msg)

    def _run_components(self, concept_type: str, run_id: str) -> list[dict[str, Any]]:
        return [
            record
            for record in self._records(concept_type)
            if str(record["frontmatter"].get("run") or "") == run_id
        ]

    @staticmethod
    def _slug(value: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return normalized[:48].rstrip("-")

    @staticmethod
    def _render_markdown(frontmatter: dict[str, Any], body: str) -> str:
        lines = ["---"]
        for key, value in frontmatter.items():
            encoded = json.dumps(value, ensure_ascii=False)
            lines.append(f"{key}: {encoded}")
        lines.extend(["---", "", body.rstrip(), ""])
        return "\n".join(lines)
