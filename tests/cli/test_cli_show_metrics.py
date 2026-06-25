"""Tests for show-metrics CLI command."""

from __future__ import annotations

from uuid import uuid4

from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.cli.main import show_metrics
from core.contracts.metadata import Metadata
from core.domain.ids import SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData
from core.workflow.models import Workflow, WorkflowRunContext


def _run_workflow(bootstrap) -> None:
    factory = ApplicationFactory()
    engine = factory.create_workflow_engine(
        bootstrap.registry().get_use_case("run_analysis"),
        bootstrap.event_bus(),
        bootstrap.transaction_unit_of_work(),
        bootstrap.metrics_collector(),
    )
    context = WorkflowRunContext(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=SessionId.new(),
        user_id=UserId.new(),
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Metrics CLI Workflow",
        capabilities=("stub.analysis",),
    )
    engine.run(workflow, context).unwrap()


def test_cli_show_metrics_empty(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = show_metrics(metrics_collector=bootstrap.metrics_collector())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Metrics" in captured.out
    assert "(no metrics)" in captured.out


def test_cli_show_metrics_lists_collected_values(capsys) -> None:
    bootstrap = Bootstrap().build()
    _run_workflow(bootstrap)

    exit_code = show_metrics(metrics_collector=bootstrap.metrics_collector())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Metric" in captured.out
    assert "Count" in captured.out
    assert "Average" in captured.out
    assert "workflow.started" in captured.out
    assert "workflow.completed" in captured.out
    assert "transaction.committed" in captured.out
