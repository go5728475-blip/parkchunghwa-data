"""Tests for provider section enrichment in RunAnalysis pipeline."""

from __future__ import annotations

from uuid import uuid4

from core.application.commands import RunAnalysis
from core.application.result import Success
from core.bootstrap.bootstrap import Bootstrap
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId
from core.domain.models import SectionSource, TraceStep
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
        birth_data=BirthData(year=1996, month=6, day=6, hour=6, minute=6),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability=capability,
        provider_id=ProviderId(value=provider_id) if provider_id else None,
    )


def test_plugin_only_produces_single_plugin_section() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(_run_analysis(provider_id=None))

    assert isinstance(result, Success)
    response = result.unwrap()
    assert response.analysis_result is not None
    assert len(response.analysis_result.sections) == 1
    assert response.analysis_result.sections[0].source is SectionSource.PLUGIN
    assert response.analysis_result.sections[0].content == "wealth placeholder"
    assert response.analysis_result.trace[0].step.value == "PLUGIN"
    assert response.analysis_result.trace[0].source == "wealth.analysis"


def test_plugin_and_provider_adds_provider_section() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _run_analysis(provider_id="openai.stub"),
    )

    assert isinstance(result, Success)
    analysis_result = result.unwrap().analysis_result
    assert analysis_result is not None
    assert len(analysis_result.sections) == 2
    assert analysis_result.sections[0].source is SectionSource.PLUGIN
    assert analysis_result.sections[1].source is SectionSource.PROVIDER
    assert "openai stub placeholder response" in analysis_result.sections[1].content


def test_provider_does_not_modify_plugin_section() -> None:
    bootstrap = Bootstrap().build()
    plugin_only = bootstrap.command_bus().dispatch(_run_analysis()).unwrap()
    enriched = bootstrap.command_bus().dispatch(
        _run_analysis(provider_id="openai.stub"),
    ).unwrap()

    plugin_section = plugin_only.analysis_result.sections[0]
    enriched_plugin_section = enriched.analysis_result.sections[0]

    assert plugin_section.content == enriched_plugin_section.content
    assert plugin_section.title == enriched_plugin_section.title
    assert plugin_section.source == enriched_plugin_section.source
    assert plugin_section.capability == enriched_plugin_section.capability


def test_trace_records_plugin_then_provider_order() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _run_analysis(provider_id="claude.stub"),
    ).unwrap()

    assert result.analysis_result is not None
    steps = [entry.step for entry in result.analysis_result.trace]
    assert steps[0] is TraceStep.PLUGIN
    assert steps[1] is TraceStep.PROVIDER
    assert steps[2] is TraceStep.REPORT


def test_analysis_result_section_order_plugin_before_provider() -> None:
    bootstrap = Bootstrap().build()
    sections = bootstrap.command_bus().dispatch(
        _run_analysis(provider_id="gemini.stub"),
    ).unwrap().analysis_result.sections

    assert sections[0].source is SectionSource.PLUGIN
    assert sections[1].source is SectionSource.PROVIDER
