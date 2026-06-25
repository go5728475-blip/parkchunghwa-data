"""Tests for report summary generation."""

from __future__ import annotations

from core.application.report_builder import ReportBuilder, _build_summary
from core.domain.xai import build_plugin_analysis_section, build_provider_analysis_section
from core.domain.ids import ProviderId


def test_build_summary_counts_plugin_and_provider_sections() -> None:
    plugin_section = build_plugin_analysis_section(
        capability="wealth.analysis",
        title="Wealth",
        content="wealth placeholder",
        plugin_id="wealth.stub",
    )
    provider_section = build_provider_analysis_section(
        plugin_section=plugin_section,
        provider_id=ProviderId(value="openai.stub"),
        capability="wealth.analysis",
        content="enrichment",
    )
    summary = _build_summary((plugin_section, provider_section))

    assert "총 2개 분석이 수행되었습니다" in summary
    assert "Plugin 1개" in summary
    assert "Provider 설명 1개" in summary


def test_build_empty_summary() -> None:
    summary = ReportBuilder().build_empty().summary

    assert "총 0개 분석이 수행되었습니다" in summary
    assert "Plugin 0개" in summary
    assert "Provider 설명 0개" in summary
