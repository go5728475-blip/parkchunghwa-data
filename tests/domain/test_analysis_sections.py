"""Tests for analysis section domain models."""

from __future__ import annotations

import pytest

from core.domain.ids import SectionId
from core.domain.models import AnalysisResult, AnalysisSection, SectionSource, TraceStep
from core.domain.xai import (
    build_plugin_analysis_section,
    build_plugin_trace_entry,
    build_provider_analysis_section,
    build_provider_trace_entry,
)
from core.domain.ids import ProviderId


def test_analysis_section_requires_content() -> None:
    with pytest.raises(ValueError, match="Content cannot be empty"):
        build_plugin_analysis_section(
            capability="wealth.analysis",
            title="Wealth",
            content="",
            plugin_id="wealth.stub",
        )


def test_analysis_result_requires_sections() -> None:
    with pytest.raises(ValueError, match="at least one section"):
        AnalysisResult(sections=())


def test_analysis_result_preserves_section_order() -> None:
    plugin_section = build_plugin_analysis_section(
        capability="wealth.analysis",
        title="Plugin Result",
        content="wealth placeholder",
        plugin_id="wealth.stub",
    )
    provider_section = build_provider_analysis_section(
        plugin_section=plugin_section,
        provider_id=ProviderId(value="openai.stub"),
        capability="wealth.analysis",
        content="enrichment placeholder",
    )
    result = AnalysisResult(
        sections=(plugin_section, provider_section),
        trace=(
            build_plugin_trace_entry("wealth.analysis"),
            build_provider_trace_entry(ProviderId(value="openai.stub")),
        ),
    )

    assert result.sections[0].source is SectionSource.PLUGIN
    assert result.sections[1].source is SectionSource.PROVIDER
    assert result.trace[0].step is TraceStep.PLUGIN
    assert result.trace[1].step is TraceStep.PROVIDER
