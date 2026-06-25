"""Tests for Markdown report exporter."""

from __future__ import annotations

from core.report.exporters.markdown_exporter import MarkdownReportExporter


def test_markdown_export_structure(plugin_and_provider_report) -> None:
    output = MarkdownReportExporter().export(plugin_and_provider_report)

    assert output.startswith(f"# {plugin_and_provider_report.title}")
    assert "## Summary" in output
    assert "## TOC" in output
    assert "## 재물" in output
    assert "### Plugin" in output
    assert "### Provider" in output
    assert "### Confidence" in output
    assert "### Reasoning" in output
    assert "### Evidence" in output
    assert "## Trace" in output


def test_markdown_export_empty_report(empty_report) -> None:
    output = MarkdownReportExporter().export(empty_report)

    assert "## Summary" in output
    assert "(empty)" in output


def test_markdown_export_plugin_only(plugin_only_report) -> None:
    output = MarkdownReportExporter().export(plugin_only_report)

    assert "### Plugin" in output
    assert "### Provider" not in output
    assert "wealth placeholder" in output


def test_markdown_export_includes_reasoning(plugin_and_provider_report) -> None:
    output = MarkdownReportExporter().export(plugin_and_provider_report)

    assert "Plugin generated canonical analysis" in output


def test_markdown_export_includes_trace(plugin_and_provider_report) -> None:
    output = MarkdownReportExporter().export(plugin_and_provider_report)

    assert "PLUGIN |" in output
    assert "PROVIDER |" in output
