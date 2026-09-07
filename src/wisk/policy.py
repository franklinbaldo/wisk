"""Composable context, access, and output policies for SessionTypes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from okf_parser import load_bundle

from wisk.session import SessionWisk

_POLICY_KEYS = ("context_policy", "access_policy", "output_policy")
_OUTPUT_FIELDS = {
    "Experience": "experience_path",
    "LoopRun": "run_path",
    "RunReading": "run_path",
    "RunGoal": "run_path",
    "RunDecision": "run_path",
    "RunEvidence": "run_path",
    "RunCheck": "run_path",
    "RunOutcome": "run_path",
    "Handoff": "handoff_path",
    "WikiEntry": "wiki_path",
    "AgentSkill": "skill_path",
    "SkillProposal": "proposal_path",
    "SkillEvaluation": "evaluation_path",
    "SessionType": "session_type_path",
    "RunSpec": "run_spec_path",
    "ContextPolicy": "context_policy_path",
    "AccessPolicy": "access_policy_path",
    "OutputPolicy": "output_policy_path",
    "CadencePolicy": "cadence_policy_path",
}
_DEFAULT_OUTPUTS = {
    "Experience": "experiences/records",
    "LoopRun": "experiences/runs",
    "RunReading": "experiences/runs",
    "RunGoal": "experiences/runs",
    "RunDecision": "experiences/runs",
    "RunEvidence": "experiences/runs",
    "RunCheck": "experiences/runs",
    "RunOutcome": "experiences/runs",
    "Handoff": "experiences/handoffs",
    "WikiEntry": "wiki/entries",
    "AgentSkill": "skills/active",
    "SkillProposal": "skills/proposals",
    "SkillEvaluation": "skills/evaluations",
    "SessionType": "skills/session-types",
    "RunSpec": "skills/run-specs",
    "ContextPolicy": "skills/policies/context",
    "AccessPolicy": "skills/policies/access",
    "OutputPolicy": "skills/policies/output",
    "CadencePolicy": "skills/policies/cadence",
}


class PolicyWisk(SessionWisk):
    """Session runtime that resolves, explains, and applies policy composition."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> PolicyWisk:
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    def effective_session_type(self, identifier: str) -> dict[str, Any]:
        session = super().effective_session_type(identifier)
        session["policies"] = {
            key: self._resolve_policy(key, str(session.get(key) or "")) for key in _POLICY_KEYS
        }
        return session

    def _resolve_policy(self, key: str, identifier: str) -> dict[str, Any] | None:
        if not identifier:
            return None
        concept_type = {
            "context_policy": "ContextPolicy",
            "access_policy": "AccessPolicy",
            "output_policy": "OutputPolicy",
        }[key]
        record = self._find_record(concept_type, identifier)
        result = dict(record["frontmatter"])
        result["id"] = str(result.get("id") or record["id"])
        result["path"] = record["path"]
        return result

    def policy_for(self, session_type_id: str | None = None) -> dict[str, Any]:
        """Return the effective policies for one SessionType."""
        session = self._select_session_type(session_type_id)
        return {"session_type": session["id"], **session.get("policies", {})}

    def _context_records(self, concept_type: str) -> list[dict[str, Any]]:
        """Expose authored concept identity independently from storage layout."""
        records: list[dict[str, Any]] = []
        for record in self._records(concept_type):
            frontmatter = record["frontmatter"]
            records.append(
                {
                    "id": str(frontmatter.get("id") or record["id"]),
                    "type": concept_type,
                    "title": record["title"],
                    "path": record["path"],
                }
            )
        return records

    def _normalize_context_records(
        self, concept_type: str, selected: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Keep retrieval relevance while replacing path-derived ids with authored ids."""
        available = self._context_records(concept_type)
        by_path = {record["path"]: record for record in available}
        normalized = [by_path.get(str(record.get("path") or ""), record) for record in selected]
        return normalized or available

    def context(self, task: str, session_type_id: str | None = None) -> dict[str, Any]:
        """Return context plus explicit policy guidance for the selected session."""
        result = super().context(task)
        session = self._select_session_type(session_type_id)
        policies = session.get("policies", {})
        context_policy = policies.get("context_policy")
        access_policy = policies.get("access_policy")
        result["session_type"] = session["id"]
        result["session_purpose"] = str(session.get("purpose") or "")
        result["session_nudges"] = list(session.get("nudges", []))
        result["context_policy"] = context_policy
        result["access_policy"] = access_policy

        surfaces = {
            "skills": ("skills", "AgentSkill"),
            "wiki": ("wiki", "WikiEntry"),
            "experiences": ("recent_experiences", "Experience"),
            "handoffs": ("active_handoffs", "Handoff"),
            "run-specs": ("run_specs", "RunSpec"),
        }
        if context_policy:
            include = {str(item) for item in context_policy.get("include", [])}
            exclude = {str(item) for item in context_policy.get("exclude", [])}
            mode = str(context_policy.get("mode") or "advisory")

            # Advisory policy does not restrict host access, but declared surfaces
            # still get stable authored identities and a useful fallback context.
            for category in include:
                key, concept_type = surfaces.get(category, ("", ""))
                if key and concept_type and category != "handoffs":
                    normalized = self._normalize_context_records(
                        concept_type, list(result.get(key, []))
                    )
                    result[key] = normalized[:5] if category == "experiences" else normalized

            if mode == "curated":
                for category, (key, _) in surfaces.items():
                    if category in exclude or (include and category not in include):
                        result[key] = []
        return result

    def output_path(self, concept_type: str, session_type_id: str | None = None) -> str:
        """Resolve the semantic output directory for a concept type."""
        fallback = _DEFAULT_OUTPUTS.get(concept_type, concept_type.lower())
        try:
            session = self._select_session_type(session_type_id)
        except ValueError:
            return fallback
        policy = session.get("policies", {}).get("output_policy")
        field = _OUTPUT_FIELDS.get(concept_type)
        if not policy or field is None:
            return fallback
        value = str(policy.get(field) or "")
        return value.strip("/") or fallback

    def preview_experience(self, **kwargs: Any) -> dict[str, str]:
        """Preview Experience in the policy-selected experience namespace."""
        preview = super().preview_experience(**kwargs)
        filename = Path(preview["path"]).name
        relative = Path(self.output_path("Experience")) / filename
        target = self.root_path / relative
        if target.exists():
            raise FileExistsError(target)
        preview["path"] = relative.as_posix()
        return preview

    def start_run(
        self,
        task: str,
        run_spec_id: str | None = None,
        session_type_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a session and place its LoopRun in the configured run namespace."""
        result = super().start_run(task, run_spec_id, session_type_id)
        old_path = Path(result["path"])
        target_dir = self.root_path / self.output_path("LoopRun", result["session_type"])
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / old_path.name
        old_path.replace(target)
        self._reload()
        result["path"] = str(target)
        result["check"] = self.check_run(result["run_id"])
        return result

    def create_handoff(self, **kwargs: Any) -> dict[str, Any]:
        """Create a Handoff and route it under experiences/handoffs by policy."""
        result = super().create_handoff(**kwargs)
        old_path = Path(result["path"])
        target_dir = self.root_path / self.output_path("Handoff")
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / old_path.name
        old_path.replace(target)
        self._reload()
        result["path"] = str(target)
        return result
