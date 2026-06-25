"""Tests for transaction-status CLI command."""

from __future__ import annotations

from uuid import uuid4

from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.cli.main import transaction_status
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData
from core.workflow.models import Workflow, WorkflowRunContext


def _run_workflow_with_uow(bootstrap) -> None:
    factory = ApplicationFactory()
    engine = factory.create_workflow_engine(
        bootstrap.registry().get_use_case("run_analysis"),
        bootstrap.event_bus(),
        bootstrap.transaction_unit_of_work(),
    )
    context = WorkflowRunContext(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=SessionId.new(),
        user_id=UserId.new(),
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Transaction Status Workflow",
        capabilities=("stub.analysis",),
    )
    engine.run(workflow, context).unwrap()


def test_cli_transaction_status_initial_state(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = transaction_status(unit_of_work=bootstrap.transaction_unit_of_work())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Transaction Status" in captured.out
    assert "Active:      False" in captured.out
    assert "Committed:   False" in captured.out
    assert "RolledBack:  False" in captured.out
    assert "StartedAt:   -" in captured.out
    assert "FinishedAt:  -" in captured.out


def test_cli_transaction_status_after_workflow_commit(capsys) -> None:
    bootstrap = Bootstrap().build()
    _run_workflow_with_uow(bootstrap)

    exit_code = transaction_status(unit_of_work=bootstrap.transaction_unit_of_work())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Committed:   True" in captured.out
    assert "Active:      False" in captured.out
    assert "StartedAt:" in captured.out
    assert "FinishedAt:" in captured.out


def test_cli_transaction_status_after_workflow_rollback(capsys) -> None:
    bootstrap = Bootstrap().build()
    factory = ApplicationFactory()
    engine = factory.create_workflow_engine(
        bootstrap.registry().get_use_case("run_analysis"),
        bootstrap.event_bus(),
        bootstrap.transaction_unit_of_work(),
    )
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Rollback Status Workflow",
        capabilities=("wealth.analysis",),
    )
    context = WorkflowRunContext(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=SessionId.new(),
        user_id=UserId.new(),
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )
    engine.run(
        workflow,
        context,
        provider_id=ProviderId(value="missing.provider"),
    )

    exit_code = transaction_status(unit_of_work=bootstrap.transaction_unit_of_work())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RolledBack:  True" in captured.out


def test_cli_run_workflow_updates_transaction_status(capsys) -> None:
    bootstrap = Bootstrap().build()
    factory = ApplicationFactory()
    engine = factory.create_workflow_engine(
        bootstrap.registry().get_use_case("run_analysis"),
        bootstrap.event_bus(),
        bootstrap.transaction_unit_of_work(),
    )
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="CLI Workflow",
        capabilities=("stub.analysis",),
    )
    context = WorkflowRunContext(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=SessionId.new(),
        user_id=UserId.new(),
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )
    engine.run(workflow, context).unwrap()

    exit_code = transaction_status(unit_of_work=bootstrap.transaction_unit_of_work())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Committed:   True" in captured.out
