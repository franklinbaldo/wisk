from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

from wisk import Wisk
from wisk.bootstrap import init_repository
from wisk.execution import ExecutionPersistenceError
from wisk.mcp import mcp
from wisk.models import generate_pydantic_code, get_schema_contracts

ROOT = Path(__file__).parent.parent


def _runtime(tmp_path: Path) -> tuple[Path, Wisk, str]:
    result = init_repository(tmp_path)
    assert result["status"] == "initialized"
    knowledge = tmp_path / ".wisk/knowledge"
    ws = Wisk.open(knowledge)
    started = ws.start_run(
        "Exercise RFC 0003 command execution",
        run_spec_id="run-specs/work",
        session_type_id="session-types/standard-work",
    )
    return knowledge, ws, str(started["run_id"])


def test_execute_command_records_raw_fact_without_inventing_semantics(tmp_path: Path) -> None:
    knowledge, ws, run = _runtime(tmp_path)

    result = ws.execute_command(
        [sys.executable, "-c", "print('hello from worker')"],
        run=run,
        cwd=tmp_path,
        why="Exercise the command wrapper",
        expect="The command prints one line and exits zero",
    )

    assert result["exit_code"] == 0
    assert result["stdout"] == "hello from worker\n"
    assert result["projections"] == {
        "evidence": [],
        "checks": [],
        "observations": [],
        "skill_uses": [],
    }

    trace = Wisk.open(knowledge).run_trace(run)
    assert len(trace["executions"]) == 1
    execution = trace["executions"][0]
    assert execution["argv"][:2] == [sys.executable, "-c"]
    assert execution["exit_code"] == 0
    assert execution["why"] == "Exercise the command wrapper"
    assert execution["expect"] == "The command prints one line and exits zero"
    assert execution["stdout_bytes"] == len(b"hello from worker\n")
    assert execution["stdout_digest"].startswith("sha256:")
    assert trace["evidence"] == []
    assert trace["checks"] == []
    assert Wisk.open(knowledge).check_run(run)["counts"]["executions"] == 1


def test_explicit_projections_link_execution_to_semantic_records(tmp_path: Path) -> None:
    knowledge, ws, run = _runtime(tmp_path)

    result = ws.execute_command(
        [sys.executable, "-c", "print('verified')"],
        run=run,
        cwd=tmp_path,
        evidence=["execution"],
        checks=["verification"],
        observe="friction",
        note="The verification needs an explicit subprocess in this fixture.",
        impact="low",
        using=["skill-adopt-wisk-consumer@1.1.0"],
    )

    assert result["exit_code"] == 0
    assert len(result["projections"]["evidence"]) == 1
    assert len(result["projections"]["checks"]) == 1
    assert len(result["projections"]["observations"]) == 1
    assert len(result["projections"]["skill_uses"]) == 1

    trace = Wisk.open(knowledge).run_trace(run)
    execution_id = trace["executions"][0]["id"]
    assert trace["evidence"][0]["reference"] == execution_id
    assert trace["checks"][0]["status"] == "pass"
    assert trace["checks"][0]["evidence"] == trace["evidence"][0]["id"]
    assert trace["observations"][0]["kind"] == "friction"
    assert trace["skill_uses"][0]["skill_version"] == "1.1.0"


def test_tdd_red_is_evidence_without_becoming_a_passing_check(tmp_path: Path) -> None:
    knowledge, ws, run = _runtime(tmp_path)

    result = ws.execute_command(
        [sys.executable, "-c", "raise SystemExit(3)"],
        run=run,
        cwd=tmp_path,
        expect="The regression reproducer exits non-zero before the fix",
        evidence=["red-test"],
    )

    assert result["exit_code"] == 3
    trace = Wisk.open(knowledge).run_trace(run)
    assert [item["kind"] for item in trace["evidence"]] == ["red-test"]
    assert trace["checks"] == []


def test_explicit_check_maps_exit_code_deterministically(tmp_path: Path) -> None:
    knowledge, ws, run = _runtime(tmp_path)

    result = ws.execute_command(
        [sys.executable, "-c", "raise SystemExit(2)"],
        run=run,
        cwd=tmp_path,
        checks=["verification"],
    )

    assert result["exit_code"] == 2
    trace = Wisk.open(knowledge).run_trace(run)
    assert trace["checks"][0]["status"] == "fail"
    assert trace["evidence"][0]["kind"] == "execution"
    assert Wisk.open(knowledge).check_run(run)["conformant"] is False


def test_invalid_skill_version_is_rejected_before_command_effect(tmp_path: Path) -> None:
    _, ws, run = _runtime(tmp_path)
    marker = tmp_path / "should-not-exist"

    with pytest.raises(ValueError, match="skill version does not match"):
        ws.execute_command(
            [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"],
            run=run,
            cwd=tmp_path,
            using=["skill-adopt-wisk-consumer@99.0.0"],
        )

    assert not marker.exists()


def test_persistence_failure_reports_that_command_effect_may_have_occurred(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, ws, run = _runtime(tmp_path)
    marker = tmp_path / "command-ran"

    def fail_record(**_: object) -> dict[str, object]:
        raise RuntimeError("simulated persistence failure")

    monkeypatch.setattr(ws, "_record_raw_component", fail_record)

    with pytest.raises(ExecutionPersistenceError) as excinfo:
        ws.execute_command(
            [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"],
            run=run,
            cwd=tmp_path,
        )

    assert marker.exists()
    assert excinfo.value.effect_may_have_occurred is True


def test_cli_run_executes_direct_argv_and_persists_trace(tmp_path: Path) -> None:
    knowledge, _, run = _runtime(tmp_path)
    completed = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "wisk.cli",
            "run",
            "--run",
            run,
            "--path",
            str(knowledge),
            "--why",
            "CLI smoke",
            "--",
            sys.executable,
            "-c",
            "print('cli-ok')",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "cli-ok\n"
    trace = Wisk.open(knowledge).run_trace(run)
    execution = trace["executions"][-1]
    assert execution["why"] == "CLI smoke"
    assert execution["argv"] == [sys.executable, "-c", "print('cli-ok')"]


def test_run_execution_is_a_normative_generated_schema_contract() -> None:
    code = generate_pydantic_code(ROOT / "knowledge")
    assert "class RunExecutionConcept(BaseModel):" in code
    contracts = get_schema_contracts(ROOT / "knowledge")
    contract_types = {item.concept_type for item in contracts}
    assert "RunExecution" in contract_types


def test_mcp_exposes_real_execution_only_as_an_explicit_tool() -> None:
    async def _check() -> None:
        names = {tool.name for tool in await mcp.list_tools()}
        assert "wisk_run" in names
        assert "wisk_run_trace" in names

    asyncio.run(_check())
