"""Tests for report builder."""

from __future__ import annotations

from core.application.report_builder import ReportBuilder
from core.bootstrap.factory import ApplicationFactory
from core.domain.ids import ProviderId
from core.domain.models import AnalysisResult, SectionSource
from core.domain.xai import (
    build_plugin_analysis_section,
    build_plugin_trace_entry,
    build_provider_analysis_section,
    build_provider_trace_entry,
)


def _plugin_section(capability: str, content: str, plugin_id: str, title: str) -> object:
    return build_plugin_analysis_section(
        capability=capability,
        title=title,
        content=content,
        plugin_id=plugin_id,
    )


def _merge_results(*results: AnalysisResult) -> AnalysisResult:
    sections: list[object] = []
    trace = []
    for result in results:
        sections.extend(result.sections)
        trace.extend(result.trace)
    return AnalysisResult(sections=tuple(sections), trace=tuple(trace))


def test_empty_report() -> None:
    report = ReportBuilder().build_empty()

    assert report.sections == ()
    assert report.toc == ()
    assert "0개 분석" in report.summary
    assert "Plugin 0개" in report.summary


def test_plugin_only_report() -> None:
    analysis_result = AnalysisResult(
        sections=(_plugin_section("wealth.analysis", "wealth placeholder", "wealth.stub", "Wealth"),),
        trace=(build_plugin_trace_entry("wealth.analysis"),),
    )
    report = ReportBuilder().build(analysis_result)

    assert len(report.sections) == 1
    assert len(report.capability_groups) == 1
    assert report.sections[0].content == "wealth placeholder"
    assert "Plugin 1개" in report.summary
    assert "Provider 설명 0개" in report.summary


def test_plugin_and_provider_report() -> None:
    plugin_section = _plugin_section(
        "wealth.analysis",
        "wealth placeholder",
        "wealth.stub",
        "Wealth",
    )
    provider_section = build_provider_analysis_section(
        plugin_section=plugin_section,
        provider_id=ProviderId(value="openai.stub"),
        capability="wealth.analysis",
        content="openai enrichment",
    )
    analysis_result = AnalysisResult(
        sections=(plugin_section, provider_section),
        trace=(
            build_plugin_trace_entry("wealth.analysis"),
            build_provider_trace_entry(ProviderId(value="openai.stub")),
        ),
    )
    report = ReportBuilder().build(analysis_result)

    assert len(report.sections) == 2
    assert report.sections[0].generated_by == SectionSource.PLUGIN.value
    assert report.sections[1].generated_by == SectionSource.PROVIDER.value
    assert "Plugin 1개" in report.summary
    assert "Provider 설명 1개" in report.summary


def test_summary_generation() -> None:
    plugin_section = _plugin_section("wealth.analysis", "wealth", "wealth.stub", "Wealth")
    provider_section = build_provider_analysis_section(
        plugin_section=plugin_section,
        provider_id=ProviderId(value="openai.stub"),
        capability="wealth.analysis",
        content="enrichment",
    )
    report = ReportBuilder().build(
        AnalysisResult(sections=(plugin_section, provider_section), trace=()),
    )

    assert "총 2개 분석이 수행되었습니다" in report.summary


def test_toc_generation() -> None:
    wealth = _plugin_section("wealth.analysis", "wealth", "wealth.stub", "Wealth")
    career = _plugin_section("career.analysis", "career", "career.stub", "Career")
    relationship = _plugin_section(
        "relationship.analysis",
        "relationship",
        "relationship.stub",
        "Relationship",
    )
    analysis_result = _merge_results(
        AnalysisResult(sections=(wealth,), trace=()),
        AnalysisResult(sections=(career,), trace=()),
        AnalysisResult(sections=(relationship,), trace=()),
    )
    report = ReportBuilder().build(analysis_result)

    toc_titles = [entry.title for entry in report.toc]
    assert toc_titles == ["재물", "직업", "관계", "종합"]


def test_capability_grouping_and_section_order() -> None:
    wealth_plugin = _plugin_section("wealth.analysis", "wealth", "wealth.stub", "Wealth")
    wealth_provider = build_provider_analysis_section(
        plugin_section=wealth_plugin,
        provider_id=ProviderId(value="openai.stub"),
        capability="wealth.analysis",
        content="wealth enrichment",
    )
    career_plugin = _plugin_section("career.analysis", "career", "career.stub", "Career")
    career_provider = build_provider_analysis_section(
        plugin_section=career_plugin,
        provider_id=ProviderId(value="claude.stub"),
        capability="career.analysis",
        content="career enrichment",
    )
    analysis_result = AnalysisResult(
        sections=(wealth_plugin, wealth_provider, career_plugin, career_provider),
        trace=(),
    )
    report = ReportBuilder().build(analysis_result)

    assert len(report.capability_groups) == 2
    assert report.capability_groups[0].label == "재물"
    assert report.capability_groups[1].label == "직업"
    assert report.capability_groups[0].sections[0].generated_by == SectionSource.PLUGIN.value
    assert report.capability_groups[0].sections[1].generated_by == SectionSource.PROVIDER.value
    assert report.sections[0].content == "wealth"
    assert report.sections[1].content == "wealth enrichment"
    assert report.sections[2].content == "career"
    assert report.sections[3].content == "career enrichment"


def test_factory_registers_report_builder() -> None:
    builder = ApplicationFactory().create_report_builder()
    assert isinstance(builder, ReportBuilder)
