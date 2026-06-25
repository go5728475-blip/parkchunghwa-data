"""Tests for JSON report exporter."""

from __future__ import annotations

import json

from core.report.exporters.json_exporter import JsonReportExporter
from tests.report.conftest import parse_json_export


def test_json_export_plugin_and_provider(plugin_and_provider_report) -> None:
    output = JsonReportExporter().export(plugin_and_provider_report)
    payload = parse_json_export(output)

    assert payload["title"] == plugin_and_provider_report.title
    assert payload["summary"] == plugin_and_provider_report.summary
    assert len(payload["toc"]) == 1
    assert len(payload["capability_groups"]) == 1
    assert len(payload["sections"]) == 2
    assert payload["sections"][0]["explanation"]["generated_by"] == "PLUGIN"
    assert payload["sections"][1]["explanation"]["generated_by"] == "PROVIDER"
    assert payload["sections"][0]["explanation"]["confidence"] == 0.75
    assert payload["sections"][0]["explanation"]["reasoning"]
    assert payload["sections"][0]["explanation"]["evidence"]
    assert len(payload["trace"]) == 2


def test_json_export_empty_report(empty_report) -> None:
    payload = parse_json_export(JsonReportExporter().export(empty_report))

    assert payload["sections"] == []
    assert payload["toc"] == []
    assert payload["trace"] == []
    assert "0개 분석" in payload["summary"]


def test_json_export_plugin_only(plugin_only_report) -> None:
    payload = parse_json_export(JsonReportExporter().export(plugin_only_report))

    assert len(payload["sections"]) == 1
    assert payload["sections"][0]["explanation"]["generated_by"] == "PLUGIN"
    assert len(payload["trace"]) == 1


def test_json_export_is_valid_json(plugin_and_provider_report) -> None:
    output = JsonReportExporter().export(plugin_and_provider_report)
    json.loads(output)
