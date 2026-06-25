"""Tests for show-events CLI command."""

from __future__ import annotations

from uuid import uuid4

from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.cli.main import run_workflow, show_events
from core.contracts.metadata import Metadata
from core.domain.ids import SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData
from core.workflow.engine import WorkflowEngine
from core.workflow.models import Workflow, WorkflowRunContext


def test_cli_show_events_after_workflow(capsys) -> None:
    bootstrap = Bootstrap().build()
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
        name="CLI Event Workflow",
        capabilities=("stub.analysis",),
    )
    engine.run(workflow, context).unwrap()

    exit_code = show_events(bootstrap.event_bus())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Recent Domain Events" in captured.out
    assert "WorkflowStarted" in captured.out
    assert "AnalysisCompleted" in captured.out


def test_cli_show_events_empty_bus(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = show_events(bootstrap.event_bus())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "(no events)" in captured.out


def test_cli_run_workflow_publishes_events(capsys) -> None:
    exit_code = run_workflow(capabilities=("stub.analysis",), provider_id=None)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Workflow Summary" in captured.out
