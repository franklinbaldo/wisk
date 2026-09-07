"""FastMCP server for wisk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from wisk import Wisk

mcp = FastMCP(name="wisk")
_WRITE_ANNOTATIONS = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": False,
}


def _get_runtime(path: str | Path = "knowledge") -> Wisk:
    return Wisk.open(Path(path))


@mcp.tool(
    name="wisk_inventory",
    description="Get concept counts grouped by concept type in the Wisk OKF bundle.",
    annotations={"readOnlyHint": True},
)
def wisk_inventory(path: str = "knowledge") -> dict[str, int]:
    return _get_runtime(path).inventory()


@mcp.tool(
    name="wisk_context",
    description=(
        "Retrieve task-relevant RunSpecs, active handoffs, skills, wiki knowledge, and recent "
        "experiences for contract-guided agent execution."
    ),
    annotations={"readOnlyHint": True},
)
def wisk_context(
    task: str,
    session_type: str | None = None,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).context(task, session_type)


@mcp.tool(
    name="wisk_start",
    description=(
        "Create an incomplete LoopRun scaffold using an optional SessionType and governing RunSpec."
    ),
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_start(
    task: str,
    run_spec: str | None = None,
    session_type: str | None = None,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).start_run(task, run_spec, session_type)


@mcp.tool(
    name="wisk_check",
    description=(
        "Validate a live LoopRun and return unmet RunSpec requirements plus the next action."
    ),
    annotations={"readOnlyHint": True},
)
def wisk_check(run: str, path: str = "knowledge") -> dict[str, Any]:
    return _get_runtime(path).check_run(run)


@mcp.tool(
    name="wisk_session_eligibility",
    description="Explain why a SessionType is or is not currently eligible to run.",
    annotations={"readOnlyHint": True},
)
def wisk_session_eligibility(
    session_type: str,
    requested: bool = False,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).session_eligibility(session_type, requested=requested)


@mcp.tool(
    name="wisk_next_session",
    description="Return the highest-priority automatically eligible SessionType.",
    annotations={"readOnlyHint": True},
)
def wisk_next_session(path: str = "knowledge") -> dict[str, Any] | None:
    return _get_runtime(path).next_session()


@mcp.tool(
    name="wisk_start_next_session",
    description="Select the highest-priority eligible SessionType and start its pinned LoopRun.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_start_next_session(
    task: str,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).start_next_session(task)


@mcp.tool(
    name="wisk_run_reading",
    description="Record a typed RunReading and attach it to an existing live LoopRun.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_run_reading(
    run: str,
    component_id: str,
    kind: str,
    subject: str,
    reference: str,
    finding: str,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).record_run_reading(
        run=run,
        component_id=component_id,
        kind=kind,
        subject=subject,
        reference=reference,
        finding=finding,
    )


@mcp.tool(
    name="wisk_run_goal",
    description="Record a typed RunGoal and attach it to an existing live LoopRun.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_run_goal(
    run: str,
    component_id: str,
    kind: str,
    goal: str,
    rationale: str,
    success_signal: str,
    status: str = "active",
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).record_run_goal(
        run=run,
        component_id=component_id,
        kind=kind,
        goal=goal,
        rationale=rationale,
        success_signal=success_signal,
        status=status,
    )


@mcp.tool(
    name="wisk_run_goal_status",
    description="Update an existing RunGoal to the state reached by its live LoopRun.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_run_goal_status(
    run: str,
    goal: str,
    status: str,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).update_run_goal_status(run=run, goal=goal, status=status)


@mcp.tool(
    name="wisk_run_decision",
    description="Record a typed RunDecision and attach it to an existing live LoopRun.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_run_decision(
    run: str,
    component_id: str,
    question: str,
    decision: str,
    rationale: str,
    goal: str | None = None,
    alternatives: list[str] | None = None,
    evidence: list[str] | None = None,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).record_run_decision(
        run=run,
        component_id=component_id,
        question=question,
        decision=decision,
        rationale=rationale,
        goal=goal,
        alternatives=alternatives,
        evidence=evidence,
    )


@mcp.tool(
    name="wisk_run_evidence",
    description="Record typed RunEvidence and attach it to an existing live LoopRun.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_run_evidence(
    run: str,
    component_id: str,
    kind: str,
    reference: str,
    summary: str,
    goal: str | None = None,
    decision: str | None = None,
    observed_at: str | None = None,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).record_run_evidence(
        run=run,
        component_id=component_id,
        kind=kind,
        reference=reference,
        summary=summary,
        goal=goal,
        decision=decision,
        observed_at=observed_at,
    )


@mcp.tool(
    name="wisk_run_check_record",
    description="Record a typed RunCheck verification and attach it to a live LoopRun.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_run_check_record(
    run: str,
    component_id: str,
    kind: str,
    procedure: str,
    result: str,
    status: str,
    evidence: str | None = None,
    goal: str | None = None,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).record_run_check(
        run=run,
        component_id=component_id,
        kind=kind,
        procedure=procedure,
        result=result,
        status=status,
        evidence=evidence,
        goal=goal,
    )


@mcp.tool(
    name="wisk_run_outcome",
    description="Record the RunOutcome that closes a contract-ready LoopRun.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_run_outcome(
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
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).record_run_outcome(
        run=run,
        component_id=component_id,
        result_state=result_state,
        work_status=work_status,
        summary=summary,
        next_move=next_move,
        goals_advanced=goals_advanced,
        evidence=evidence,
        checks=checks,
        experiences_recorded=experiences_recorded,
    )


@mcp.tool(
    name="wisk_handoffs",
    description="List active cross-session handoffs, ranking task-relevant work first.",
    annotations={"readOnlyHint": True},
)
def wisk_handoffs(task: str | None = None, path: str = "knowledge") -> list[dict[str, Any]]:
    return _get_runtime(path).active_handoffs(task)


@mcp.tool(
    name="wisk_handoff_create",
    description="Create a validated active Handoff for material work left by a LoopRun.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_handoff_create(
    handoff_id: str,
    title: str,
    created_by_run: str,
    state: str,
    next_action: str,
    references: list[str] | None = None,
    goals: list[str] | None = None,
    target_session_type: str | None = None,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).create_handoff(
        handoff_id=handoff_id,
        title=title,
        created_by_run=created_by_run,
        state=state,
        next_action=next_action,
        references=references,
        goals=goals,
        target_session_type=target_session_type,
    )


@mcp.tool(
    name="wisk_handoff_continue",
    description=("Archive an active Handoff and record the later LoopRun that resumed the work."),
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_handoff_continue(
    handoff: str,
    continued_by_run: str,
    resolution: str,
    path: str = "knowledge",
) -> dict[str, Any]:
    return _get_runtime(path).continue_handoff(
        handoff=handoff,
        continued_by_run=continued_by_run,
        resolution=resolution,
    )


@mcp.tool(
    name="wisk_experience_preview",
    description="Preview an OKF Experience document without writing it to the bundle.",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def wisk_experience_preview(
    experience_id: str,
    title: str,
    timestamp: str,
    status: str,
    body: str,
    path: str = "knowledge",
    skill_used: str | None = None,
    skill_version: str | None = None,
    task: str | None = None,
    error_code: str | None = None,
    context: str | None = None,
    run: str | None = None,
) -> dict[str, str]:
    return _get_runtime(path).preview_experience(
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


@mcp.tool(
    name="wisk_experience_record",
    description="Write one validated OKF Experience document to the Wisk bundle.",
    annotations=_WRITE_ANNOTATIONS,
)
def wisk_experience_record(
    experience_id: str,
    title: str,
    timestamp: str,
    status: str,
    body: str,
    path: str = "knowledge",
    skill_used: str | None = None,
    skill_version: str | None = None,
    task: str | None = None,
    error_code: str | None = None,
    context: str | None = None,
    run: str | None = None,
) -> dict[str, str | bool]:
    return _get_runtime(path).record_experience(
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
