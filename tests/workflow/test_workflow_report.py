"""Tests for workflow report integration."""

from __future__ import annotations

import json
from uuid import uuid4

from core.application.report_builder import ReportBuilder
from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId, WorkflowId
from core.domain.value_objects import BirthData
from core.report.exporters.json_exporter import JsonReportExporter
from core.workflow.models import Workflow, WorkflowRunContext


def _run_workflow(capabilities: tuple[str, ...], provider_id: str | None = None):
    bootstrap = Bootstrap().build()
    factory = ApplicationFactory()
    engine = factory.create_workflow_engine(bootstrap.registry().get_use_case("run_analysis"))
    builder = factory.create_workflow_builder()
    user_id = UserId.new()
    context = WorkflowRunContext(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=SessionId.new(),
        user_id=user_id,
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Report Workflow",
        capabilities=capabilities,
    )
    provider = ProviderId(value=provider_id) if provider_id else None
    workflow_result = engine.run(workflow, context, provider_id=provider).unwrap()
    built_report = builder.build(workflow, workflow_result)
    return workflow, workflow_result, built_report


def test_build_many_integrates_multiple_capabilities() -> None:
    _, _, built_report = _run_workflow(
        ("wealth.analysis", "career.analysis", "relationship.analysis"),
    )

    assert len(built_report.capability_groups) == 3
    assert len(built_report.sections) == 3
    toc_titles = [entry.title for entry in built_report.toc]
    assert toc_titles == ["재물", "직업", "관계", "종합"]


def test_workflow_report_preserves_capability_order() -> None:
    workflow, _, built_report = _run_workflow(("career.analysis", "wealth.analysis"))

    assert [group.capability for group in built_report.capability_groups] == list(
        workflow.capabilities,
    )


def test_workflow_report_includes_trace() -> None:
    _, workflow_result, built_report = _run_workflow(("wealth.analysis",))

    assert built_report.trace == workflow_result.trace
    assert any(entry.source == "workflow" for entry in built_report.trace)


def test_workflow_report_plugin_and_provider() -> None:
    _, _, built_report = _run_workflow(("wealth.analysis",), provider_id="openai.stub")

    assert len(built_report.sections) == 2
    assert "Provider 설명 1개" in built_report.summary


def test_report_builder_build_many_directly() -> None:
    bootstrap = Bootstrap().build()
    factory = ApplicationFactory()
    engine = factory.create_workflow_engine(bootstrap.registry().get_use_case("run_analysis"))
    user_id = UserId.new()
    context = WorkflowRunContext(
        metadata=Metadata(correlation_id=uuid4()),
        session_id=SessionId.new(),
        user_id=user_id,
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="Direct Build Many",
        capabilities=("wealth.analysis", "career.analysis"),
    )
    workflow_result = engine.run(workflow, context).unwrap()
    built_report = ReportBuilder().build_many(
        workflow_result.analysis_results,
        capability_order=workflow.capabilities,
        trace=workflow_result.trace,
    )

    assert len(built_report.capability_groups) == 2


def test_workflow_result_exports_to_json() -> None:
    _, _, built_report = _run_workflow(
        ("wealth.analysis", "career.analysis"),
        provider_id="openai.stub",
    )
    payload = json.loads(JsonReportExporter().export(built_report))

    assert payload["title"]
    assert len(payload["capability_groups"]) == 2
    assert payload["trace"]
    assert any(
        section["explanation"]["generated_by"] == "PROVIDER"
        for section in payload["sections"]
    )


def test_factory_registers_workflow_builder() -> None:
    builder = ApplicationFactory().create_workflow_builder()
    from core.workflow.report_builder import WorkflowReportBuilder

    assert isinstance(builder, WorkflowReportBuilder)
