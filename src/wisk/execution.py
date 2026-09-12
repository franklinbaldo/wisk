"""RFC 0003 real-command execution layered on RFC 0007 Work traces."""

from __future__ import annotations

import hashlib
import shlex
import subprocess  # nosec B404
import uuid
from pathlib import Path
from typing import Any

from okf_parser import load_bundle

from wisk.work_run import WorkRunWisk


class ExecutionPersistenceError(RuntimeError):
    """Persistence failed after a command may already have changed external state."""

    def __init__(self, message: str, *, effect_may_have_occurred: bool) -> None:
        super().__init__(message)
        self.effect_may_have_occurred = effect_may_have_occurred


class ExecutionWisk(WorkRunWisk):
    """Wisk runtime that can observe real argv execution without inventing semantics."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> ExecutionWisk:
        """Open an execution-aware runtime without narrowing back to WorkRunWisk."""
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    def execute_command(
        self,
        argv: list[str] | tuple[str, ...],
        *,
        run: str | None = None,
        task: str | None = None,
        run_spec: str | None = None,
        session_type: str | None = None,
        cwd: str | Path | None = None,
        why: str | None = None,
        expect: str | None = None,
        evidence: list[str] | tuple[str, ...] | None = None,
        checks: list[str] | tuple[str, ...] | None = None,
        observe: str | None = None,
        note: str | None = None,
        impact: str = "medium",
        using: list[str] | tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """Execute direct argv, persist RunExecution, then add explicitly requested projections."""
        command = [str(part) for part in argv]
        if not command or not command[0].strip():
            raise ValueError("argv must contain at least one executable")

        evidence_kinds = self._clean_kinds(evidence)
        check_kinds = self._clean_kinds(checks)
        if observe is not None and not observe.strip():
            raise ValueError("observe must contain a non-empty RunObservation kind")
        if observe is not None and not (note or "").strip():
            raise ValueError("--observe requires a concise --note")
        if observe is None and note is not None:
            raise ValueError("--note requires --observe")
        prepared_skills = [self._prepare_skill_use(item) for item in (using or [])]

        run_id = self._resolve_execution_run(
            run=run,
            task=task,
            run_spec=run_spec,
            session_type=session_type,
        )
        check_before = self.check_run(run_id)
        next_before = self._next_label(check_before)
        cwd_path = Path(cwd or Path.cwd()).resolve()
        if not cwd_path.is_dir():
            raise ValueError(f"cwd is not a directory: {cwd_path}")

        git_before = self._git_state(cwd_path)
        started_at = self._now()
        launched = False
        launch_error: str | None = None
        stdout = b""
        stderr = b""
        exit_code: int | None = None
        try:
            completed = subprocess.run(  # nosec B603
                command,
                cwd=cwd_path,
                stdin=None,
                capture_output=True,
                check=False,
                shell=False,
            )
            launched = True
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = int(completed.returncode)
        except OSError as exc:
            launch_error = f"{type(exc).__name__}: {exc}"
        finished_at = self._now()
        git_after = self._git_state(cwd_path)

        execution_component = f"execution-{uuid.uuid4().hex[:12]}"
        fields: dict[str, Any] = {
            "executor": "argv",
            "argv": command,
            "cwd": str(cwd_path),
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": exit_code,
            "launch_error": launch_error,
            "why": why.strip() if why and why.strip() else None,
            "expect": expect.strip() if expect and expect.strip() else None,
            "next_before": next_before,
            "stdout_bytes": len(stdout),
            "stderr_bytes": len(stderr),
            "stdout_digest": self._digest(stdout),
            "stderr_digest": self._digest(stderr),
            "git_head_before": git_before.get("head"),
            "git_dirty_before": git_before.get("dirty"),
            "git_head_after": git_after.get("head"),
            "git_dirty_after": git_after.get("dirty"),
        }

        try:
            execution = self._record_raw_component(
                concept_type="RunExecution",
                run_identifier=run_id,
                component_id=execution_component,
                prefix="run-executions",
                label="execution",
                fields=fields,
            )
            projections = self._project_execution(
                run_id=run_id,
                execution_id=str(execution["id"]),
                execution_component=execution_component,
                argv=command,
                exit_code=exit_code,
                launch_error=launch_error,
                finished_at=finished_at,
                evidence_kinds=evidence_kinds,
                check_kinds=check_kinds,
                observe=observe,
                note=note,
                impact=impact,
                prepared_skills=prepared_skills,
            )
            check_after = self.check_run(run_id)
            next_after = self._next_label(check_after)
            self._update_execution_next(str(execution["id"]), next_after)
        except Exception as exc:
            if isinstance(exc, ExecutionPersistenceError):
                raise
            raise ExecutionPersistenceError(
                "Command execution completed, but Wisk could not persist the complete trace; "
                f"effect_may_have_occurred={launched}",
                effect_may_have_occurred=launched,
            ) from exc

        return {
            "run": run_id,
            "execution": str(execution["id"]),
            "argv": command,
            "cwd": str(cwd_path),
            "exit_code": exit_code,
            "launch_error": launch_error,
            "started_at": started_at,
            "finished_at": finished_at,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "stdout_bytes": len(stdout),
            "stderr_bytes": len(stderr),
            "stdout_digest": self._digest(stdout),
            "stderr_digest": self._digest(stderr),
            "projections": projections,
            "next_before": next_before,
            "next_after": next_after,
            "check": check_after,
            "effect_may_have_occurred": launched,
        }

    def _trace_mapping(self) -> dict[str, str]:
        """Extend the parser-materialized Work trace with observed command executions."""
        return {**super()._trace_mapping(), "executions": "RunExecution"}

    def check_run(self, run_id_or_path: str) -> dict[str, Any]:
        """Expose RunExecution counts without making execution a universal RunSpec requirement."""
        result = super().check_run(run_id_or_path)
        run = self._find_record("LoopRun", run_id_or_path)
        run_id = str(run["frontmatter"].get("id") or run["id"])
        counts = dict(result.get("counts") or {})
        counts["executions"] = len(self._run_components("RunExecution", run_id))
        result["counts"] = counts
        return result

    def _resolve_execution_run(
        self,
        *,
        run: str | None,
        task: str | None,
        run_spec: str | None,
        session_type: str | None,
    ) -> str:
        if run is not None:
            record = self._find_record("LoopRun", run)
            return str(record["frontmatter"].get("id") or record["id"])
        started = self.start(task, run_spec=run_spec, session_type=session_type)
        run_id = started.get("run") or started.get("run_id")
        if not run_id:
            raise ValueError("Wisk did not resolve an active LoopRun for command execution")
        return str(run_id)

    def _project_execution(
        self,
        *,
        run_id: str,
        execution_id: str,
        execution_component: str,
        argv: list[str],
        exit_code: int | None,
        launch_error: str | None,
        finished_at: str,
        evidence_kinds: list[str],
        check_kinds: list[str],
        observe: str | None,
        note: str | None,
        impact: str,
        prepared_skills: list[tuple[str, str, str]],
    ) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {
            "evidence": [],
            "checks": [],
            "observations": [],
            "skill_uses": [],
        }
        objective_summary = self._execution_summary(argv, exit_code, launch_error)
        evidence_ids: list[str] = []
        for index, kind in enumerate(evidence_kinds, start=1):
            recorded = self.record_run_evidence(
                run=run_id,
                component_id=f"{execution_component}-evidence-{index}-{kind}",
                kind=kind,
                reference=execution_id,
                summary=objective_summary,
                observed_at=finished_at,
            )
            evidence_id = str(recorded["id"])
            evidence_ids.append(evidence_id)
            result["evidence"].append(evidence_id)

        if check_kinds and not evidence_ids:
            recorded = self.record_run_evidence(
                run=run_id,
                component_id=f"{execution_component}-evidence-execution",
                kind="execution",
                reference=execution_id,
                summary=objective_summary,
                observed_at=finished_at,
            )
            evidence_id = str(recorded["id"])
            evidence_ids.append(evidence_id)
            result["evidence"].append(evidence_id)

        if exit_code is None:
            check_status = "inconclusive"
        elif exit_code == 0:
            check_status = "pass"
        else:
            check_status = "fail"
        procedure = shlex.join(argv)
        for index, kind in enumerate(check_kinds, start=1):
            recorded = self.record_run_check(
                run=run_id,
                component_id=f"{execution_component}-check-{index}-{kind}",
                kind=kind,
                procedure=procedure,
                result=objective_summary,
                status=check_status,
                evidence=evidence_ids[0] if evidence_ids else None,
                observed_at=finished_at,
            )
            result["checks"].append(str(recorded["id"]))

        if observe is not None:
            recorded = self.record_run_observation(
                run=run_id,
                component_id=f"{execution_component}-observation-{observe}",
                kind=observe,
                summary=str(note),
                impact=impact,
                observed_at=finished_at,
            )
            result["observations"].append(str(recorded["id"]))

        for index, (skill, version, status) in enumerate(prepared_skills, start=1):
            recorded = self.record_run_skill_use(
                run=run_id,
                component_id=f"{execution_component}-skill-{index}",
                skill=skill,
                skill_version=version,
                skill_status=status,
                observed_at=finished_at,
                notes=f"Declared via wisk run --using for {execution_id}.",
            )
            result["skill_uses"].append(str(recorded["id"]))
        return result

    def _prepare_skill_use(self, value: str) -> tuple[str, str, str]:
        raw = str(value).strip()
        if "@" not in raw:
            raise ValueError("--using must use the form <skill-id>@<version>")
        skill, version = raw.rsplit("@", 1)
        if not skill or not version:
            raise ValueError("--using must use the form <skill-id>@<version>")
        record = self._find_record("AgentSkill", skill)
        fm = record["frontmatter"]
        canonical = str(fm.get("id") or record["id"])
        actual_version = str(fm.get("version") or "")
        status = str(fm.get("status") or "")
        if actual_version and actual_version != version:
            raise ValueError(
                f"skill version does not match AgentSkill {canonical}: "
                f"expected {actual_version}, got {version}"
            )
        if status not in {"active", "experimental"}:
            raise ValueError(f"AgentSkill {canonical} is not executable in status {status!r}")
        return canonical, version, status

    def _update_execution_next(self, execution: str, next_after: str | None) -> None:
        record = self._find_record("RunExecution", execution)
        path = self.root_path / record["path"]
        previous = path.read_text(encoding="utf-8")
        frontmatter = dict(record["frontmatter"])
        if next_after is None:
            frontmatter.pop("next_after", None)
        else:
            frontmatter["next_after"] = next_after
        body = self._body_from_document(previous)
        path.write_text(self._render_markdown(frontmatter, body), encoding="utf-8", newline="\n")
        try:
            self._require_conformant_bundle()
        except Exception:
            path.write_text(previous, encoding="utf-8", newline="\n")
            self._reload()
            raise
        self._reload()

    @staticmethod
    def _clean_kinds(values: list[str] | tuple[str, ...] | None) -> list[str]:
        result = [str(value).strip() for value in (values or [])]
        if any(not value for value in result):
            raise ValueError("projection kinds must be non-empty")
        return result

    @staticmethod
    def _digest(data: bytes) -> str:
        return f"sha256:{hashlib.sha256(data).hexdigest()}"

    @staticmethod
    def _execution_summary(
        argv: list[str],
        exit_code: int | None,
        launch_error: str | None,
    ) -> str:
        command = shlex.join(argv)
        if exit_code is not None:
            return f"`{command}` exited {exit_code}."
        return f"`{command}` could not be launched: {launch_error or 'unknown launcher error'}."

    @staticmethod
    def _next_label(check: dict[str, Any]) -> str | None:
        action = check.get("next_action")
        if not isinstance(action, dict):
            return None
        value = action.get("requirement") or action.get("kind")
        return str(value) if value is not None else None

    @staticmethod
    def _git_state(cwd: Path) -> dict[str, Any]:
        try:
            head = subprocess.run(  # nosec B603 B607
                ["git", "rev-parse", "HEAD"],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                text=True,
                timeout=3,
            )
            if head.returncode != 0:
                return {}
            dirty = subprocess.run(  # nosec B603 B607
                ["git", "status", "--porcelain"],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                text=True,
                timeout=3,
            )
            return {
                "head": head.stdout.strip(),
                "dirty": bool(dirty.stdout) if dirty.returncode == 0 else None,
            }
        except (OSError, subprocess.TimeoutExpired):
            return {}
