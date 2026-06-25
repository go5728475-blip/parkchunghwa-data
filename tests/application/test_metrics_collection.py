"""Tests for metrics collection across application layers."""

from __future__ import annotations

from uuid import uuid4

from core.application.commands import RunAnalysis
from core.application.report_builder import ReportBuilder
from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData, EngineContext
from core.report.factory import create_exporter
from core.workflow.models import Workflow, WorkflowRunContext


def _bootstrap():
    return Bootstrap().build()


def _run_analysis_command(
    bootstrap,
    *,
    capability: str = "wealth.analysis",
    provider_id: str | None = "openai.stub",
):
    user_id = UserId.new()
    session_id = SessionId.new()
    command = RunAnalysis(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability=capability,
        provider_id=ProviderId(value=provider_id) if provider_id else None,
    )
    return bootstrap.command_bus().dispatch(command)


def _metric_names(bootstrap) -> set[str]:
    return {metric.metric_name for metric in bootstrap.metrics_collector().list()}


def test_analysis_metrics_collected() -> None:
    bootstrap = _bootstrap()
    _run_analysis_command(bootstrap, provider_id="openai.stub")

    names = _metric_names(bootstrap)
    assert "analysis.started" in names
    assert "analysis.completed" in names
    assert "analysis.duration" in names
    assert "capability.executed" in names
    assert "provider.called" in names
    assert "provider.completed" in names


def test_analysis_failure_metrics_collected() -> None:
    bootstrap = _bootstrap()
    _run_analysis_command(bootstrap, provider_id="missing.provider")

    names = _metric_names(bootstrap)
    assert "analysis.failed" in names


def test_report_metrics_collected() -> None:
    bootstrap = _bootstrap()
    response = _run_analysis_command(bootstrap).unwrap()
    metrics = bootstrap.metrics_collector()
    builder = ApplicationFactory().create_report_builder(
        bootstrap.event_bus(),
        metrics,
    )

    builder.build(response.analysis_result)

    names = _metric_names(bootstrap)
    assert "report.built" in names
    assert "report.duration" in names


def test_export_metrics_collected() -> None:
    bootstrap = _bootstrap()
    response = _run_analysis_command(bootstrap).unwrap()
    metrics = bootstrap.metrics_collector()
    builder = ReportBuilder(bootstrap.event_bus(), metrics)
    built_report = builder.build(response.analysis_result)
    exporter = create_exporter(
        "json",
        event_bus=bootstrap.event_bus(),
        metrics_collector=metrics,
    )

    exporter.export(built_report)

    names = _metric_names(bootstrap)
    assert "report.exported" in names
    assert "report.export.duration" in names


def test_workflow_metrics_collected() -> None:
    bootstrap = _bootstrap()
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
        name="Metrics Workflow",
        capabilities=("stub.analysis",),
    )

    engine.run(workflow, context).unwrap()

    names = _metric_names(bootstrap)
    assert "workflow.started" in names
    assert "workflow.completed" in names
    assert "workflow.duration" in names
    assert "transaction.started" in names
    assert "transaction.committed" in names
    assert "transaction.duration" in names


def test_trace_entries_share_correlation_id() -> None:
    correlation_id = uuid4()
    bootstrap = _bootstrap()
    factory = ApplicationFactory()
    engine = factory.create_workflow_engine(
        bootstrap.registry().get_use_case("run_analysis"),
        bootstrap.event_bus(),
        bootstrap.transaction_unit_of_work(),
        bootstrap.metrics_collector(),
    )
    context = WorkflowRunContext(
        metadata=Metadata(correlation_id=correlation_id),
        session_id=SessionId.new(),
        user_id=UserId.new(),
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Correlation Workflow",
        capabilities=("stub.analysis",),
    )

    workflow_result = engine.run(workflow, context).unwrap()

    correlated = [
        entry.correlation_id
        for entry in workflow_result.trace
        if entry.correlation_id is not None
    ]
    assert correlated
    assert all(value == str(correlation_id) for value in correlated)
