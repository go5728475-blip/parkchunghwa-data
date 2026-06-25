"""Tests for HTML report exporter."""

from __future__ import annotations

from core.report.exporters.html_exporter import HtmlReportExporter


def test_html_export_structure(plugin_and_provider_report) -> None:
    output = HtmlReportExporter().export(plugin_and_provider_report)

    assert output.startswith("<!DOCTYPE html>")
    assert '<html lang="ko">' in output
    assert "<h1>" in output
    assert "<h2>Summary</h2>" in output
    assert "<h2>TOC</h2>" in output
    assert "<h2>재물</h2>" in output
    assert "<h3>Plugin</h3>" in output
    assert "<h3>Provider</h3>" in output
    assert "<h3>Confidence</h3>" in output
    assert "<h3>Reasoning</h3>" in output
    assert "<h3>Evidence</h3>" in output
    assert "<h2>Trace</h2>" in output
    assert "<style" not in output.lower()
    assert "<script" not in output.lower()


def test_html_export_empty_report(empty_report) -> None:
    output = HtmlReportExporter().export(empty_report)

    assert "<p>(empty)</p>" in output


def test_html_export_plugin_only(plugin_only_report) -> None:
    output = HtmlReportExporter().export(plugin_only_report)

    assert "<h3>Plugin</h3>" in output
    assert "<h3>Provider</h3>" not in output


def test_html_export_includes_reasoning(plugin_and_provider_report) -> None:
    output = HtmlReportExporter().export(plugin_and_provider_report)

    assert "Plugin generated canonical analysis" in output


def test_html_export_includes_trace(plugin_and_provider_report) -> None:
    output = HtmlReportExporter().export(plugin_and_provider_report)

    assert "<time>" in output
    assert "PLUGIN" in output
