"""Tests for domain event publication across application layers."""

from __future__ import annotations

import json
from uuid import uuid4

from core.application.commands import RunAnalysis
from core.application.report_builder import ReportBuilder
from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData, EngineContext
from core.report.exporters.json_exporter import JsonReportExporter
from core.workflow.models import ExecutionMode, Workflow, WorkflowRunContext


def _bootstrap():
    return Bootstrap().build()


def _run_analysis(
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
    return bootstrap.command_bus().dispatch(command).unwrap()


def test_workflow_started_and_completed_events() -> None:
    bootstrap = _bootstrap()
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
        name="Event Workflow",
        capabilities=("wealth.analysis",),
    )
    engine.run(workflow, context).unwrap()

    event_types = [event.event_type for event in bootstrap.event_bus().recent_events()]
    assert "WorkflowStarted" in event_types
    assert "WorkflowCompleted" in event_types


def test_analysis_completed_event_published() -> None:
    bootstrap = _bootstrap()
    _run_analysis(bootstrap)

    event_types = [event.event_type for event in bootstrap.event_bus().recent_events()]
    assert event_types.index("AnalysisStarted") < event_types.index("AnalysisCompleted")


def test_provider_events_published() -> None:
    bootstrap = _bootstrap()
    response = _run_analysis(bootstrap, provider_id="openai.stub")

    event_types = [event.event_type for event in bootstrap.event_bus().recent_events()]
    assert "ProviderCalled" in event_types
    assert "ProviderCompleted" in event_types
    assert response.analysis_result is not None
    assert any(
        entry.event_type == "ProviderCompleted"
        for entry in response.analysis_result.trace
        if entry.event_id
    )


def test_report_built_event_published() -> None:
    bootstrap = _bootstrap()
    response = _run_analysis(bootstrap, provider_id=None, capability="stub.analysis")
    builder = ApplicationFactory().create_report_builder(bootstrap.event_bus())
    built_report = builder.build(response.analysis_result)

    event_types = [event.event_type for event in bootstrap.event_bus().recent_events()]
    assert "ReportBuilt" in event_types
    assert any(entry.event_type == "ReportBuilt" for entry in built_report.trace)


def test_report_exported_event_published() -> None:
    bootstrap = _bootstrap()
    response = _run_analysis(bootstrap, provider_id=None, capability="stub.analysis")
    builder = ApplicationFactory().create_report_builder(bootstrap.event_bus())
    built_report = builder.build(response.analysis_result)
    JsonReportExporter(bootstrap.event_bus(), export_format="json").export(built_report)

    event_types = [event.event_type for event in bootstrap.event_bus().recent_events()]
    assert "ReportExported" in event_types


def test_capability_executed_event_published() -> None:
    bootstrap = _bootstrap()
    _run_analysis(bootstrap, provider_id=None, capability="stub.analysis")

    event_types = [event.event_type for event in bootstrap.event_bus().recent_events()]
    assert "CapabilityExecuted" in event_types


def test_event_order_for_analysis_with_provider() -> None:
    bootstrap = _bootstrap()
    _run_analysis(bootstrap, provider_id="openai.stub")

    event_types = [event.event_type for event in bootstrap.event_bus().recent_events()]
    assert event_types.index("AnalysisStarted") < event_types.index("ProviderCalled")
    assert event_types.index("ProviderCalled") < event_types.index("CapabilityExecuted")
    assert event_types.index("CapabilityExecuted") < event_types.index("ProviderCompleted")
    assert event_types.index("ProviderCompleted") < event_types.index("AnalysisCompleted")


def test_export_output_still_valid_json() -> None:
    bootstrap = _bootstrap()
    response = _run_analysis(bootstrap, provider_id=None, capability="stub.analysis")
    built_report = ReportBuilder(bootstrap.event_bus()).build(response.analysis_result)
    output = JsonReportExporter(bootstrap.event_bus()).export(built_report)
    payload = json.loads(output)
    assert payload["trace"]


def test_publish_persists_events_in_store() -> None:
    bootstrap = _bootstrap()
    _run_analysis(bootstrap, provider_id=None, capability="stub.analysis")

    stored = bootstrap.published_event_store().list()
    event_types = [event.event_type for event in stored]

    assert "AnalysisStarted" in event_types
    assert "AnalysisCompleted" in event_types
