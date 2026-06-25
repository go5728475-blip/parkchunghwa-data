"""Tests for export-report CLI command."""

from __future__ import annotations

import json

from core.cli.main import export_report


def test_cli_export_report_json(capsys) -> None:
    exit_code = export_report(
        export_format="json",
        capability="wealth.analysis",
        provider_id="openai.stub",
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["title"]
    assert payload["sections"]
    assert payload["trace"]


def test_cli_export_report_markdown(capsys) -> None:
    exit_code = export_report(
        export_format="markdown",
        capability="wealth.analysis",
        provider_id="openai.stub",
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.startswith("# ")
    assert "## Summary" in captured.out


def test_cli_export_report_html(capsys) -> None:
    exit_code = export_report(
        export_format="html",
        capability="stub.analysis",
        provider_id=None,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.startswith("<!DOCTYPE html>")


def test_cli_export_report_unsupported_format(capsys) -> None:
    exit_code = export_report(export_format="pdf")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "[MASTER ENGINE] ExportReport failed" in captured.out
