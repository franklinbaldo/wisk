"""CLI interface for wisk using Cyclopts."""

from __future__ import annotations

import json
import sys
from typing import Any

import cyclopts

from wisk import __version__
from wisk.bootstrap import DEFAULT_PROFILE, init_repository, upgrade_repository
from wisk.migrate import migrate_bundle
from wisk.operations import runtime as _runtime
from wisk.operations import start as start_operation

app = cyclopts.App(
    name="wisk",
    help="Contract-guided agent execution and persistent learning runtime built on OKF.",
    version=__version__,
)
experience_app = app.command(
    cyclopts.App(
        name="experience",
        help="Legacy 0.3.x Experience compatibility operations; new Work uses LoopRun traces.",
    )
)
handoff_app = app.command(
    cyclopts.App(name="handoff", help="Create, list, and continue cross-session Handoffs.")
)
session_app = app.command(
    cyclopts.App(name="session", help="Inspect scheduling and start eligible SessionTypes.")
)
run_app = app.command(
    cyclopts.App(name="run", help="Record and inspect typed state in a Work LoopRun trace.")
)


def _print_json(result: Any) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


def _wiki(path: str | None):
    return _runtime(path)


@app.command
def info() -> None:
    """Show wisk version and runtime information."""
    print(f"wisk runtime v{__version__} (OKF-backed)")


@app.command(name="init")
def init_command(repository: str = ".", *, profile: str = DEFAULT_PROFILE) -> None:
    """Initialize a repository with the managed Wisk consumer bundle."""
    _print_json(init_repository(repository, profile=profile))


@app.command
def upgrade(repository: str = ".") -> None:
    """Upgrade Wisk-managed consumer files without overwriting local state."""
    _print_json(upgrade_repository(repository))


@app.command(name="migrate")
def migrate_command(path: str = "knowledge", *, apply: bool = False) -> None:
    """Inspect/apply the conservative 0.3.x -> 0.4 RC Work-trace migration."""
    _print_json(migrate_bundle(path, apply=apply))


@app.command
def serve() -> None:
    """Start the FastMCP server over stdio."""
    from wisk.mcp import mcp

    mcp.run()


@app.command
def context(
    task: str,
    *,
    session_type: str | None = None,
    path: str | None = None,
) -> None:
    """Show role-curated contract and learned context for an agent task."""
    res = _wiki(path).context(task, session_type)
    print(f"--- Context for: {task} ---")
    print(f"SessionType: {res.get('session_type')}")
    print(f"Active handoffs ({len(res['active_handoffs'])}):")
    for handoff in res["active_handoffs"]:
        print(f"  - [{handoff['id']}] {handoff['title']} -> {handoff['next_action']}")
    print(f"RunSpecs found ({len(res['run_specs'])}):")
    for spec in res["run_specs"]:
        print(f"  - [{spec['id']}] {spec['title']}")
    print(f"Skills found ({len(res['skills'])}):")
    for skill in res["skills"]:
        print(f"  - [{skill['id']}] {skill['title']}")
    print(f"Wiki knowledge found ({len(res['wiki'])}):")
    for wiki in res["wiki"]:
        print(f"  - [{wiki['id']}] {wiki['title']}")
    work_runs = list(res.get("recent_work_runs", []))
    print(f"Closed Work traces found ({len(work_runs)}):")
    for run in work_runs:
        print(f"  - [{run['id']}] {run['title']}")
    proposals = list(res.get("skill_proposals", []))
    print(f"Skill proposals found ({len(proposals)}):")
    for proposal in proposals:
        print(f"  - [{proposal['id']}] {proposal['title']}")


@app.command
def start(
    task: str | None = None,
    legacy_run_spec: str | None = None,
    legacy_session_type: str | None = None,
    *,
    run_spec: str | None = None,
    session_type: str | None = None,
    path: str | None = None,
) -> None:
    """Start or resume the best useful Wisk session."""
    if legacy_run_spec is not None:
        if run_spec is not None:
            raise ValueError("RunSpec was provided both positionally and through --run-spec.")
        run_spec = legacy_run_spec
    if legacy_session_type is not None:
        if session_type is not None:
            raise ValueError(
                "SessionType was provided both positionally and through --session-type."
            )
        session_type = legacy_session_type
    if legacy_run_spec is not None or legacy_session_type is not None:
        print(
            "Deprecated: positional RunSpec/SessionType overrides will be removed; "
            "use --run-spec and --session-type.",
            file=sys.stderr,
        )

    _print_json(
        start_operation(
            task,
            run_spec=run_spec,
            session_type=session_type,
            path=path,
        )
    )


@app.command
def check(run: str, *, path: str | None = None) -> None:
    """Check a live run and show unsatisfied operational requirements."""
    _print_json(_wiki(path).check_run(run))


@session_app.command(name="next")
def session_next(*, path: str | None = None) -> None:
    """Show the highest-priority automatically eligible SessionType."""
    _print_json(_wiki(path).next_session())


@session_app.command(name="start-next")
def session_start_next(task: str, *, path: str | None = None) -> None:
    """Compatibility alias for the pre-RFC 0006 start-next entrypoint."""
    _print_json(start_operation(task, path=path))


@run_app.command(name="trace")
def run_trace(run: str, *, path: str | None = None) -> None:
    """Reconstruct one Work Raw Layer trace from child-owned run links."""
    _print_json(_wiki(path).run_trace(run))


@run_app.command(name="reading")
def run_reading(
    run: str,
    component_id: str,
    kind: str,
    subject: str,
    reference: str,
    finding: str,
    *,
    path: str | None = None,
) -> None:
    """Record one RunReading."""
    _print_json(
        _wiki(path).record_run_reading(
            run=run,
            component_id=component_id,
            kind=kind,
            subject=subject,
            reference=reference,
            finding=finding,
        )
    )


@run_app.command(name="goal")
def run_goal(
    run: str,
    component_id: str,
    kind: str,
    goal: str,
    rationale: str,
    success_signal: str,
    *,
    status: str = "active",
    path: str | None = None,
) -> None:
    """Record one RunGoal."""
    _print_json(
        _wiki(path).record_run_goal(
            run=run,
            component_id=component_id,
            kind=kind,
            goal=goal,
            rationale=rationale,
            success_signal=success_signal,
            status=status,
        )
    )


@run_app.command(name="goal-status")
def run_goal_status(
    run: str,
    goal: str,
    status: str,
    *,
    path: str | None = None,
) -> None:
    """Update an existing RunGoal to the state reached by the live run."""
    _print_json(_wiki(path).update_run_goal_status(run=run, goal=goal, status=status))


@run_app.command(name="decision")
def run_decision(
    run: str,
    component_id: str,
    question: str,
    decision: str,
    rationale: str,
    *,
    path: str | None = None,
    goal: str | None = None,
    alternatives: list[str] | None = None,
) -> None:
    """Record one RunDecision."""
    _print_json(
        _wiki(path).record_run_decision(
            run=run,
            component_id=component_id,
            question=question,
            decision=decision,
            rationale=rationale,
            goal=goal,
            alternatives=alternatives,
        )
    )


@run_app.command(name="evidence")
def run_evidence(
    run: str,
    component_id: str,
    kind: str,
    reference: str,
    summary: str,
    *,
    path: str | None = None,
    goal: str | None = None,
    observed_at: str | None = None,
) -> None:
    """Record one RunEvidence."""
    _print_json(
        _wiki(path).record_run_evidence(
            run=run,
            component_id=component_id,
            kind=kind,
            reference=reference,
            summary=summary,
            goal=goal,
            observed_at=observed_at,
        )
    )


@run_app.command(name="observation")
def run_observation(
    run: str,
    component_id: str,
    kind: str,
    summary: str,
    impact: str,
    *,
    path: str | None = None,
    observed_at: str | None = None,
    skill_use: str | None = None,
) -> None:
    """Record friction, surprise, near-miss, workaround, opportunity, or skill feedback."""
    _print_json(
        _wiki(path).record_run_observation(
            run=run,
            component_id=component_id,
            kind=kind,
            summary=summary,
            impact=impact,
            observed_at=observed_at,
            skill_use=skill_use,
        )
    )


@run_app.command(name="skill-use")
def run_skill_use(
    run: str,
    component_id: str,
    skill: str,
    skill_version: str,
    skill_status: str,
    *,
    path: str | None = None,
    observed_at: str | None = None,
    notes: str | None = None,
) -> None:
    """Record the exact AgentSkill version that actually guided a Work run."""
    _print_json(
        _wiki(path).record_run_skill_use(
            run=run,
            component_id=component_id,
            skill=skill,
            skill_version=skill_version,
            skill_status=skill_status,
            observed_at=observed_at,
            notes=notes,
        )
    )


@run_app.command(name="check")
def run_check_record(
    run: str,
    component_id: str,
    kind: str,
    procedure: str,
    result: str,
    status: str,
    *,
    path: str | None = None,
    evidence: str | None = None,
    goal: str | None = None,
    observed_at: str | None = None,
) -> None:
    """Record one RunCheck."""
    _print_json(
        _wiki(path).record_run_check(
            run=run,
            component_id=component_id,
            kind=kind,
            procedure=procedure,
            result=result,
            status=status,
            evidence=evidence,
            goal=goal,
            observed_at=observed_at,
        )
    )


@run_app.command(name="outcome")
def run_outcome(
    run: str,
    component_id: str,
    result_state: str,
    work_status: str,
    summary: str,
    next_move: str,
    *,
    path: str | None = None,
) -> None:
    """Record the RunOutcome that closes a contract-ready run and timestamps completion."""
    _print_json(
        _wiki(path).record_run_outcome(
            run=run,
            component_id=component_id,
            result_state=result_state,
            work_status=work_status,
            summary=summary,
            next_move=next_move,
        )
    )


@handoff_app.command(name="list")
def handoff_list(task: str | None = None, *, path: str | None = None) -> None:
    """List active handoffs, prioritizing work relevant to a task."""
    _print_json(_wiki(path).active_handoffs(task))


@handoff_app.command(name="create")
def handoff_create(
    handoff_id: str,
    title: str,
    created_by_run: str,
    state: str,
    next_action: str,
    *,
    path: str | None = None,
    references: list[str] | None = None,
    goals: list[str] | None = None,
    target_session_type: str | None = None,
) -> None:
    """Persist an active handoff emitted by one LoopRun."""
    _print_json(
        _wiki(path).create_handoff(
            handoff_id=handoff_id,
            title=title,
            created_by_run=created_by_run,
            state=state,
            next_action=next_action,
            references=references,
            goals=goals,
            target_session_type=target_session_type,
        )
    )


@handoff_app.command(name="continue")
def handoff_continue(
    handoff: str,
    continued_by_run: str,
    resolution: str,
    *,
    path: str | None = None,
) -> None:
    """Archive a handoff with provenance to the later LoopRun that resolved it."""
    _print_json(
        _wiki(path).continue_handoff(
            handoff=handoff,
            continued_by_run=continued_by_run,
            resolution=resolution,
        )
    )


@experience_app.command(name="preview")
def experience_preview(
    experience_id: str,
    title: str,
    timestamp: str,
    status: str,
    body: str,
    *,
    path: str | None = None,
    skill_used: str | None = None,
    skill_version: str | None = None,
    task: str | None = None,
    error_code: str | None = None,
    context: str | None = None,
    run: str | None = None,
) -> None:
    """Preview a legacy Experience document without changing the bundle."""
    result = _wiki(path).preview_experience(
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
    print(result["content"], end="")


@experience_app.command(name="record")
def experience_record(
    experience_id: str,
    title: str,
    timestamp: str,
    status: str,
    body: str,
    *,
    path: str | None = None,
    skill_used: str | None = None,
    skill_version: str | None = None,
    task: str | None = None,
    error_code: str | None = None,
    context: str | None = None,
    run: str | None = None,
) -> None:
    """Persist one legacy Experience document during the 0.4 RC migration window."""
    print(
        "Deprecated in 0.4: new Work sessions should use the LoopRun trace and RunSkillUse.",
        file=sys.stderr,
    )
    result = _wiki(path).record_experience(
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
    print(f"Recorded legacy Experience {result['id']} -> {result['path']}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
