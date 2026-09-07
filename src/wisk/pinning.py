"""Immutable RunSpec snapshots for historical LoopRun validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from okf_parser import load_bundle

from wisk.cadence import CadenceWisk

_LIFECYCLE_CHECK_KINDS = frozenset(
    {"handoff", "goal-state", "handoff-environment", "handoff-disposition"}
)
_PRE_RUN_LIFECYCLE_KINDS = frozenset({"handoff-environment", "handoff-disposition"})


class PinnedWisk(CadenceWisk):
    """Cadence runtime whose new LoopRuns retain their governing RunSpec contract."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> PinnedWisk:
        """Open a bundle while preserving the pinned runtime type."""
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    def start_run(
        self,
        task: str,
        run_spec_id: str | None = None,
        session_type_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a run and freeze the complete effective RunSpec frontmatter."""
        result = super().start_run(task, run_spec_id, session_type_id)
        run = self._find_record("LoopRun", result["run_id"])
        effective_spec = self.effective_run_spec(str(result["run_spec"]))
        spec_fm = {
            key: value
            for key, value in effective_spec.items()
            if key not in {"path", "inheritance"}
        }
        snapshot = self._canonical_snapshot(spec_fm)
        digest = self._snapshot_digest(snapshot)

        path = self.root_path / run["path"]
        previous = path.read_text(encoding="utf-8")
        frontmatter = dict(run["frontmatter"])
        frontmatter.update(
            {
                "run_spec_version": str(spec_fm.get("version") or ""),
                "run_spec_digest": digest,
                "run_spec_snapshot": snapshot,
            }
        )
        body = self._body_from_document(previous)
        path.write_text(self._render_markdown(frontmatter, body), encoding="utf-8")
        try:
            self._require_conformant_bundle()
        except Exception:
            path.unlink(missing_ok=True)
            self._reload()
            raise

        self._reload()
        result["run_spec_version"] = frontmatter["run_spec_version"]
        result["run_spec_digest"] = digest
        result["check"] = self.check_run(result["run_id"])
        return result

    def check_run(self, run_id_or_path: str) -> dict[str, Any]:
        """Validate a run against its pinned RunSpec, with legacy fallback."""
        base = super().check_run(run_id_or_path)
        run = self._find_record("LoopRun", run_id_or_path)
        run_fm = run["frontmatter"]
        snapshot_value = run_fm.get("run_spec_snapshot")
        if snapshot_value in {None, ""}:
            result = dict(base)
            result["run_spec_pinned"] = False
            return result

        snapshot = str(snapshot_value)
        expected_digest = str(run_fm.get("run_spec_digest") or "")
        actual_digest = self._snapshot_digest(snapshot)
        if expected_digest != actual_digest:
            return self._pinning_failure(
                base,
                run_fm,
                "Pinned RunSpec digest does not match the stored snapshot.",
            )

        try:
            pinned = json.loads(snapshot)
        except json.JSONDecodeError:
            return self._pinning_failure(
                base,
                run_fm,
                "Pinned RunSpec snapshot is not valid JSON.",
            )
        if not isinstance(pinned, dict):
            return self._pinning_failure(
                base,
                run_fm,
                "Pinned RunSpec snapshot must decode to an object.",
            )

        pinned_version = str(pinned.get("version") or "")
        if pinned_version != str(run_fm.get("run_spec_version") or ""):
            return self._pinning_failure(
                base,
                run_fm,
                "Pinned RunSpec version does not match the stored snapshot.",
            )
        pinned_id = str(pinned.get("id") or "")
        run_spec_id = str(run_fm.get("run_spec") or "")
        if pinned_id and pinned_id != run_spec_id:
            return self._pinning_failure(
                base,
                run_fm,
                "Pinned RunSpec identity does not match the LoopRun reference.",
            )

        run_id = str(run_fm.get("id") or run["id"])
        components = {
            "readings": self._run_components("RunReading", run_id),
            "goals": self._run_components("RunGoal", run_id),
            "decisions": self._run_components("RunDecision", run_id),
            "evidence": self._run_components("RunEvidence", run_id),
            "checks": self._run_components("RunCheck", run_id),
            "outcomes": self._run_components("RunOutcome", run_id),
        }
        lifecycle = [
            item for item in base["unsatisfied"] if item.get("kind") in _LIFECYCLE_CHECK_KINDS
        ]
        pre_run_lifecycle = [
            item for item in lifecycle if item.get("kind") in _PRE_RUN_LIFECYCLE_KINDS
        ]
        closing_lifecycle = [
            item for item in lifecycle if item.get("kind") not in _PRE_RUN_LIFECYCLE_KINDS
        ]
        unsatisfied = [
            *pre_run_lifecycle,
            *self._pinned_unsatisfied(pinned, components),
            *closing_lifecycle,
        ]
        structural = base["structural"]
        conformant = bool(structural["conformant"]) and not unsatisfied

        if unsatisfied:
            next_action = dict(unsatisfied[0])
        elif conformant:
            next_action = {
                "kind": "complete",
                "requirement": None,
                "message": "Run satisfies its pinned RunSpec.",
            }
        else:
            next_action = {
                "kind": "structural",
                "requirement": "okf",
                "message": "Resolve structural OKF diagnostics before continuing.",
            }

        result = dict(base)
        result.update(
            {
                "run_spec": run_spec_id,
                "run_spec_version": pinned_version,
                "run_spec_digest": expected_digest,
                "run_spec_pinned": True,
                "conformant": conformant,
                "unsatisfied": unsatisfied,
                "next_action": next_action,
                "counts": {name: len(records) for name, records in components.items()},
            }
        )
        return result

    def _pinning_failure(
        self,
        base: dict[str, Any],
        run_fm: dict[str, Any],
        message: str,
    ) -> dict[str, Any]:
        requirement = {
            "requirement": "run-spec-snapshot",
            "kind": "contract",
            "message": message,
        }
        extras = [
            item for item in base["unsatisfied"] if item.get("kind") in _LIFECYCLE_CHECK_KINDS
        ]
        result = dict(base)
        result.update(
            {
                "run_spec": str(run_fm.get("run_spec") or ""),
                "run_spec_version": str(run_fm.get("run_spec_version") or ""),
                "run_spec_digest": str(run_fm.get("run_spec_digest") or ""),
                "run_spec_pinned": True,
                "conformant": False,
                "unsatisfied": [requirement, *extras],
                "next_action": requirement,
            }
        )
        return result

    def _pinned_unsatisfied(
        self,
        spec_fm: dict[str, Any],
        components: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
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
                        "message": "RunOutcome result_state is outside the pinned RunSpec.",
                    }
                )
        return unsatisfied

    @staticmethod
    def _canonical_snapshot(frontmatter: dict[str, Any]) -> str:
        return json.dumps(
            frontmatter,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _snapshot_digest(snapshot: str) -> str:
        digest = hashlib.sha256(snapshot.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"
