"""Tests for workflow transaction boundaries."""

from __future__ import annotations

from uuid import uuid4

from core.application.result import Failure
from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData
from core.workflow.models import Workflow, WorkflowRunContext


def _workflow_context() -> WorkflowRunContext:
    return WorkflowRunContext(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=SessionId.new(),
        user_id=UserId.new(),
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )


def _workflow_engine(bootstrap):
    factory = ApplicationFactory()
    return factory.create_workflow_engine(
        bootstrap.registry().get_use_case("run_analysis"),
        bootstrap.event_bus(),
        bootstrap.transaction_unit_of_work(),
    )


def test_workflow_commit_persists_events_and_updates_context() -> None:
    bootstrap = Bootstrap().build()
    engine = _workflow_engine(bootstrap)
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Committed Workflow",
        capabilities=("stub.analysis",),
    )

    result = engine.run(workflow, _workflow_context())
    context = bootstrap.transaction_unit_of_work().context

    assert not isinstance(result, Failure)
    assert context.committed is True
    assert context.active is False
    assert len(bootstrap.published_event_store().list()) > 0


def test_workflow_commit_includes_transaction_trace() -> None:
    bootstrap = Bootstrap().build()
    engine = _workflow_engine(bootstrap)
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Trace Workflow",
        capabilities=("stub.analysis",),
    )

    workflow_result = engine.run(workflow, _workflow_context()).unwrap()
    messages = [entry.message for entry in workflow_result.trace]

    assert any("Transaction started" in message for message in messages)
    assert any("Transaction committed" in message for message in messages)


def test_workflow_rollback_on_failure() -> None:
    bootstrap = Bootstrap().build()
    engine = _workflow_engine(bootstrap)
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Rollback Workflow",
        capabilities=("wealth.analysis",),
    )

    result = engine.run(
        workflow,
        _workflow_context(),
        provider_id=ProviderId(value="missing.provider"),
    )
    context = bootstrap.transaction_unit_of_work().context

    assert isinstance(result, Failure)
    assert context.rolled_back is True
    assert context.committed is False


def test_workflow_rollback_discards_buffered_events() -> None:
    bootstrap = Bootstrap().build()
    engine = _workflow_engine(bootstrap)
    store = bootstrap.published_event_store()
    initial_count = len(store.list())
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Buffered Rollback",
        capabilities=("wealth.analysis",),
    )

    engine.run(
        workflow,
        _workflow_context(),
        provider_id=ProviderId(value="missing.provider"),
    )

    assert len(store.list()) == initial_count
