"""Tests for snapshot-status CLI command."""

from __future__ import annotations

from uuid import uuid4

from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.cli.main import snapshot_status
from core.contracts.metadata import Metadata
from core.domain.ids import SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData
from core.workflow.models import Workflow, WorkflowRunContext


def _populate_stores(bootstrap):
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
        name="Snapshot Status Workflow",
        capabilities=("stub.analysis",),
    )
    engine.run(workflow, context).unwrap()
    return workflow


def test_cli_snapshot_status_lists_aggregates(capsys) -> None:
    bootstrap = Bootstrap().build()
    _populate_stores(bootstrap)

    exit_code = snapshot_status(
        event_store=bootstrap.published_event_store(),
        snapshot_store=bootstrap.snapshot_store(),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Snapshot Status" in captured.out
    assert "Replay Start:" in captured.out


def test_cli_snapshot_status_shows_snapshot_when_policy_triggers(capsys) -> None:
    bootstrap = Bootstrap().build()
    _populate_stores(bootstrap)

    exit_code = snapshot_status(
        event_store=bootstrap.published_event_store(),
        snapshot_store=bootstrap.snapshot_store(),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Latest Snapshot:" in captured.out


def test_cli_snapshot_status_empty(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = snapshot_status(
        event_store=bootstrap.published_event_store(),
        snapshot_store=bootstrap.snapshot_store(),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "(no aggregates)" in captured.out
