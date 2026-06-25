"""Tests for workflow engine."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.application.result import Failure
from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData
from core.workflow.engine import WorkflowEngine
from core.workflow.models import ExecutionMode, Workflow, WorkflowRunContext


def _workflow_context() -> WorkflowRunContext:
    user_id = UserId.new()
    return WorkflowRunContext(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=SessionId.new(),
        user_id=user_id,
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )


def _workflow_engine() -> WorkflowEngine:
    bootstrap = Bootstrap().build()
    run_analysis = bootstrap.registry().get_use_case("run_analysis")
    return ApplicationFactory().create_workflow_engine(run_analysis)


def test_single_capability_workflow() -> None:
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Single Capability",
        capabilities=("stub.analysis",),
    )
    result = _workflow_engine().run(workflow, _workflow_context())

    assert not isinstance(result, Failure)
    workflow_result = result.unwrap()
    assert len(workflow_result.analysis_results) == 1
    assert len(workflow_result.analysis_results[0].sections) >= 1


def test_multiple_capability_workflow() -> None:
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Multi Capability",
        capabilities=("wealth.analysis", "career.analysis", "relationship.analysis"),
    )
    result = _workflow_engine().run(workflow, _workflow_context())

    workflow_result = result.unwrap()
    assert len(workflow_result.analysis_results) == 3


def test_workflow_preserves_execution_order() -> None:
    capabilities = ("wealth.analysis", "career.analysis", "relationship.analysis")
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Ordered Workflow",
        capabilities=capabilities,
    )
    result = _workflow_engine().run(workflow, _workflow_context())
    workflow_result = result.unwrap()

    observed = tuple(
        result.sections[0].capability for result in workflow_result.analysis_results
    )
    assert observed == capabilities


def test_workflow_trace_includes_execution_steps() -> None:
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Trace Workflow",
        capabilities=("wealth.analysis",),
    )
    result = _workflow_engine().run(workflow, _workflow_context())
    workflow_result = result.unwrap()

    messages = [entry.message for entry in workflow_result.trace]
    assert any("Workflow started" in message for message in messages)
    assert any("Executing capability" in message for message in messages)
    assert any("Completed capability" in message for message in messages)
    assert any("Workflow completed" in message for message in messages)


def test_workflow_with_provider() -> None:
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Provider Workflow",
        capabilities=("wealth.analysis",),
    )
    result = _workflow_engine().run(
        workflow,
        _workflow_context(),
        provider_id=ProviderId(value="openai.stub"),
    )
    workflow_result = result.unwrap()

    assert len(workflow_result.analysis_results[0].sections) == 2


def test_workflow_without_provider() -> None:
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Plugin Only Workflow",
        capabilities=("wealth.analysis",),
    )
    result = _workflow_engine().run(workflow, _workflow_context())
    workflow_result = result.unwrap()

    assert len(workflow_result.analysis_results[0].sections) == 1


def test_parallel_mode_runs_sequentially() -> None:
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Parallel Reserved",
        capabilities=("wealth.analysis", "career.analysis"),
        execution_mode=ExecutionMode.PARALLEL,
    )
    result = _workflow_engine().run(workflow, _workflow_context())

    assert not isinstance(result, Failure)
    assert len(result.unwrap().analysis_results) == 2


def test_factory_registers_workflow_engine() -> None:
    bootstrap = Bootstrap().build()
    engine = ApplicationFactory().create_workflow_engine(
        bootstrap.registry().get_use_case("run_analysis"),
    )
    assert isinstance(engine, WorkflowEngine)


def test_workflow_invalid_provider_returns_failure() -> None:
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Invalid Provider",
        capabilities=("wealth.analysis",),
    )
    result = _workflow_engine().run(
        workflow,
        _workflow_context(),
        provider_id=ProviderId(value="missing.provider"),
    )

    assert isinstance(result, Failure)
