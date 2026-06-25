"""Shared fixtures for report export tests."""

from __future__ import annotations

import json

import pytest

from core.application.report_builder import ReportBuilder
from core.domain.ids import ProviderId
from core.domain.models import AnalysisResult
from core.domain.xai import (
    build_plugin_analysis_section,
    build_plugin_trace_entry,
    build_provider_analysis_section,
    build_provider_trace_entry,
)


@pytest.fixture
def empty_report():
    return ReportBuilder().build_empty()


@pytest.fixture
def plugin_only_report():
    plugin_section = build_plugin_analysis_section(
        capability="wealth.analysis",
        title="Wealth",
        content="wealth placeholder",
        plugin_id="wealth.stub",
    )
    analysis_result = AnalysisResult(
        sections=(plugin_section,),
        trace=(build_plugin_trace_entry("wealth.analysis"),),
    )
    return ReportBuilder().build(analysis_result)


@pytest.fixture
def plugin_and_provider_report():
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
        content="openai enrichment",
    )
    analysis_result = AnalysisResult(
        sections=(plugin_section, provider_section),
        trace=(
            build_plugin_trace_entry("wealth.analysis"),
            build_provider_trace_entry(ProviderId(value="openai.stub")),
        ),
    )
    return ReportBuilder().build(analysis_result)


def parse_json_export(output: str) -> dict:
    return json.loads(output)
