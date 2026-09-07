"""SessionType and RunSpec inheritance plus LoopRun binding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from okf_parser import load_bundle

from wisk.handoff import HandoffWisk

_RUNSPEC_REQUIREMENT_FIELDS = (
    "required_reading_kinds",
    "required_goal_kinds",
    "required_evidence_kinds",
    "required_check_kinds",
)


class SessionWisk(HandoffWisk):
    """Wisk runtime with typed, inheritable session behavior."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> SessionWisk:
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    def session_types(self) -> list[dict[str, Any]]:
        return [self.effective_session_type(item["id"]) for item in self._records("SessionType")]

    def effective_session_type(self, identifier: str) -> dict[str, Any]:
        return self._resolve_session_type(identifier, stack=())

    def _resolve_session_type(self, identifier: str, stack: tuple[str, ...]) -> dict[str, Any]:
        record = self._find_record("SessionType", identifier)
        session_id = str(record["frontmatter"].get("id") or record["id"])
        if session_id in stack:
            chain = " -> ".join((*stack, session_id))
            raise ValueError(f"SessionType inheritance cycle: {chain}")

        fm = dict(record["frontmatter"])
        parent_ref = str(fm.get("extends") or "")
        effective: dict[str, Any] = {}
        if parent_ref:
            effective.update(self._resolve_session_type(parent_ref, (*stack, session_id)))

        parent_nudges = [str(item) for item in effective.get("nudges", [])]
        child_nudges = [str(item) for item in fm.get("nudges", [])]
        effective.update({key: value for key, value in fm.items() if key != "nudges"})
        effective["nudges"] = [*parent_nudges, *child_nudges]
        effective["id"] = session_id
        effective["path"] = record["path"]
        effective["inheritance"] = [*effective.get("inheritance", []), session_id]
        return effective

    def effective_run_spec(self, identifier: str) -> dict[str, Any]:
        return self._resolve_run_spec(identifier, stack=())

    def _resolve_run_spec(self, identifier: str, stack: tuple[str, ...]) -> dict[str, Any]:
        record = self._find_record("RunSpec", identifier)
        spec_id = str(record["frontmatter"].get("id") or record["id"])
        if spec_id in stack:
            chain = " -> ".join((*stack, spec_id))
            raise ValueError(f"RunSpec inheritance cycle: {chain}")

        fm = dict(record["frontmatter"])
        parent_ref = str(fm.get("parent_spec") or "")
        effective: dict[str, Any] = {}
        if parent_ref:
            effective.update(self._resolve_run_spec(parent_ref, (*stack, spec_id)))

        inherited_requirements = {
            field: [str(item) for item in effective.get(field, [])]
            for field in _RUNSPEC_REQUIREMENT_FIELDS
        }
        effective.update(
            {key: value for key, value in fm.items() if key not in _RUNSPEC_REQUIREMENT_FIELDS}
        )
        for field in _RUNSPEC_REQUIREMENT_FIELDS:
            merged = [*inherited_requirements[field]]
            for item in fm.get(field, []):
                value = str(item)
                if value not in merged:
                    merged.append(value)
            effective[field] = merged

        effective["id"] = spec_id
        effective["path"] = record["path"]
        effective["inheritance"] = [*effective.get("inheritance", []), spec_id]
        return effective

    def _select_session_type(self, requested: str | None) -> dict[str, Any]:
        if requested:
            return self.effective_session_type(requested)
        try:
            return self.effective_session_type("session-types/development")
        except ValueError:
            sessions = self._records("SessionType")
            if not sessions:
                raise ValueError(
                    "No SessionType concepts are available in the knowledge bundle."
                ) from None
            return self.effective_session_type(sessions[0]["id"])

    def start_run(
        self,
        task: str,
        run_spec_id: str | None = None,
        session_type_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a LoopRun governed by an effective SessionType."""
        session = self._select_session_type(session_type_id)
        session_spec = str(session.get("run_spec") or "")
        selected_spec = run_spec_id or session_spec or None
        result = super().start_run(task, selected_spec)

        run = self._find_record("LoopRun", result["run_id"])
        path = self.root_path / run["path"]
        previous = path.read_text(encoding="utf-8")
        frontmatter = dict(run["frontmatter"])
        spec = self.effective_run_spec(str(result["run_spec"]))
        canonical_spec_id = str(spec["id"])
        frontmatter["run_spec"] = canonical_spec_id
        frontmatter["session_type"] = session["id"]
        body = self._body_from_document(previous)
        path.write_text(self._render_markdown(frontmatter, body), encoding="utf-8")
        try:
            self._require_conformant_bundle()
        except Exception:
            path.write_text(previous, encoding="utf-8")
            self._reload()
            raise
        self._reload()

        result["run_spec"] = canonical_spec_id
        result["session_type"] = session["id"]
        result["session"] = {
            "id": session["id"],
            "purpose": str(session.get("purpose") or ""),
            "nudges": list(session.get("nudges", [])),
            "inheritance": list(session.get("inheritance", [])),
        }

        cadence = session.get("cadence") or {}
        if self._bool(cadence.get("handoff_compatible")):
            lineage = set(str(item) for item in session.get("inheritance", []))
            lineage.add(str(session["id"]))
            candidates = [
                item
                for item in self.active_handoffs(task)
                if not item.get("target_session_type")
                or str(item.get("target_session_type") or "") in lineage
            ]
            if candidates:
                selected_handoff = candidates[0]
                self.attach_handoff_to_run(
                    handoff=str(selected_handoff["id"]),
                    run=str(result["run_id"]),
                )
                result["resumed_handoff"] = selected_handoff["id"]

        result["check"] = self.check_run(result["run_id"])
        return result

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
