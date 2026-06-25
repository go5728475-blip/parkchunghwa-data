"""Tests for XAI-enabled analysis pipeline."""

from __future__ import annotations

from uuid import uuid4

from core.application.commands import RunAnalysis
from core.application.result import Success
from core.bootstrap.bootstrap import Bootstrap
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId
from core.domain.models import GeneratedBy, SectionSource, TraceStep
from core.domain.value_objects import BirthData, EngineContext


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _run_analysis(
    *,
    capability: str = "wealth.analysis",
    provider_id: str | None = None,
) -> RunAnalysis:
    user_id = UserId.new()
    session_id = SessionId.new()
    return RunAnalysis(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1997, month=7, day=7, hour=7, minute=7),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability=capability,
        provider_id=ProviderId(value=provider_id) if provider_id else None,
    )


def test_plugin_explanation_created_on_run() -> None:
    bootstrap = Bootstrap().build()
    response = bootstrap.command_bus().dispatch(_run_analysis()).unwrap()

    plugin_section = response.analysis_result.sections[0]
    assert plugin_section.explanation.generated_by is GeneratedBy.PLUGIN
    assert plugin_section.explanation.reasoning
    assert plugin_section.explanation.evidence
    assert 0.0 <= plugin_section.explanation.confidence <= 1.0


def test_provider_explanation_created_on_enrichment() -> None:
    bootstrap = Bootstrap().build()
    response = bootstrap.command_bus().dispatch(
        _run_analysis(provider_id="openai.stub"),
    ).unwrap()

    provider_section = response.analysis_result.sections[1]
    assert provider_section.explanation.generated_by is GeneratedBy.PROVIDER
    assert provider_section.explanation.reasoning
    assert provider_section.explanation.evidence


def test_provider_section_links_enriched_from_section_id() -> None:
    bootstrap = Bootstrap().build()
    response = bootstrap.command_bus().dispatch(
        _run_analysis(provider_id="claude.stub"),
    ).unwrap()

    plugin_section = response.analysis_result.sections[0]
    provider_section = response.analysis_result.sections[1]

    assert provider_section.enriched_from_section_id == plugin_section.section_id
    assert provider_section.source is SectionSource.PROVIDER


def test_provider_does_not_modify_plugin_explanation() -> None:
    bootstrap = Bootstrap().build()
    plugin_only = bootstrap.command_bus().dispatch(_run_analysis()).unwrap()
    enriched = bootstrap.command_bus().dispatch(
        _run_analysis(provider_id="openai.stub"),
    ).unwrap()

    plugin_explanation = plugin_only.analysis_result.sections[0].explanation
    enriched_explanation = enriched.analysis_result.sections[0].explanation

    assert plugin_explanation.reasoning == enriched_explanation.reasoning
    assert plugin_explanation.evidence == enriched_explanation.evidence
    assert plugin_explanation.confidence == enriched_explanation.confidence
    assert plugin_explanation.generated_by == enriched_explanation.generated_by


def test_trace_entry_order_plugin_provider_report() -> None:
    bootstrap = Bootstrap().build()
    response = bootstrap.command_bus().dispatch(
        _run_analysis(provider_id="openai.stub"),
    ).unwrap()

    pipeline_steps = [
        entry.step
        for entry in response.analysis_result.trace
        if entry.event_id is None
    ]
    assert pipeline_steps == [TraceStep.PLUGIN, TraceStep.PROVIDER, TraceStep.REPORT]
    event_types = [
        entry.event_type
        for entry in response.analysis_result.trace
        if entry.event_type is not None
    ]
    assert "AnalysisStarted" in event_types
    assert "AnalysisCompleted" in event_types


def test_report_aggregate_syncs_explanation_fields() -> None:
    bootstrap = Bootstrap().build()
    response = bootstrap.command_bus().dispatch(_run_analysis()).unwrap()
    report = bootstrap.unit_of_work().reports.get(response.report_id)

    assert report is not None
    report_section = report.sections[0]
    plugin_section = response.analysis_result.sections[0]
    assert report_section.reasoning == plugin_section.explanation.reasoning
    assert report_section.evidence == plugin_section.explanation.evidence
    assert report_section.confidence.value == plugin_section.explanation.confidence
