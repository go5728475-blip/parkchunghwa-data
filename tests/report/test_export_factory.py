"""Tests for report export factory."""

from __future__ import annotations

import pytest

from core.bootstrap.factory import ApplicationFactory
from core.report.errors import UnsupportedExportFormat
from core.report.exporters.html_exporter import HtmlReportExporter
from core.report.exporters.json_exporter import JsonReportExporter
from core.report.exporters.markdown_exporter import MarkdownReportExporter
from core.report.factory import create_exporter


@pytest.mark.parametrize(
    ("export_format", "expected_type"),
    [
        ("json", JsonReportExporter),
        ("markdown", MarkdownReportExporter),
        ("html", HtmlReportExporter),
        ("JSON", JsonReportExporter),
    ],
)
def test_create_exporter_supported_formats(export_format, expected_type) -> None:
    exporter = create_exporter(export_format)
    assert isinstance(exporter, expected_type)


def test_create_exporter_unsupported_format() -> None:
    with pytest.raises(UnsupportedExportFormat):
        create_exporter("pdf")


def test_application_factory_registers_report_exporter() -> None:
    exporter = ApplicationFactory().create_report_exporter("json")
    assert isinstance(exporter, JsonReportExporter)
