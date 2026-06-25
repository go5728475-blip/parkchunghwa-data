"""Tests for replay-events CLI command."""

from __future__ import annotations

from uuid import uuid4

from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.cli.main import replay_events
from core.contracts.metadata import Metadata
from core.domain.ids import SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData
from core.workflow.models import Workflow, WorkflowRunContext


def _populate_store(bootstrap):
    factory = ApplicationFactory()
    engine = factory.create_workflow_engine(
        bootstrap.registry().get_use_case("run_analysis"),
        bootstrap.event_bus(),
    )
    user_id = UserId.new()
    context = WorkflowRunContext(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=SessionId.new(),
        user_id=user_id,
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Replay Workflow",
        capabilities=("stub.analysis",),
    )
    engine.run(workflow, context).unwrap()
    return workflow


def test_cli_replay_events_output(capsys) -> None:
    bootstrap = Bootstrap().build()
    workflow = _populate_store(bootstrap)

    exit_code = replay_events(event_store=bootstrap.published_event_store())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Replay Summary" in captured.out
    assert "event count:" in captured.out
    assert "Replay Trace:" in captured.out
    assert "WorkflowStarted" in captured.out
    assert "AnalysisCompleted" in captured.out


def test_cli_replay_events_by_aggregate(capsys) -> None:
    bootstrap = Bootstrap().build()
    workflow = _populate_store(bootstrap)

    exit_code = replay_events(
        aggregate_id=str(workflow.workflow_id),
        event_store=bootstrap.published_event_store(),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "WorkflowStarted" in captured.out
    assert "WorkflowCompleted" in captured.out


def test_cli_replay_events_empty_store(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = replay_events(event_store=bootstrap.published_event_store())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "event count: 0" in captured.out
