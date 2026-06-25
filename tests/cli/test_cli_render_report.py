"""Tests for render-report CLI command."""

from __future__ import annotations

from core.cli.main import render_report


def test_cli_render_report_output(capsys) -> None:
    exit_code = render_report(
        capability="wealth.analysis",
        provider_id="openai.stub",
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Rendered Report" in captured.out
    assert "Title:" in captured.out
    assert "Summary:" in captured.out
    assert "TOC:" in captured.out
    assert "[재물]" in captured.out
    assert "Confidence:" in captured.out
    assert "Reasoning:" in captured.out
    assert "Evidence:" in captured.out
    assert "Trace:" in captured.out


def test_cli_render_report_plugin_only(capsys) -> None:
    exit_code = render_report(capability="stub.analysis", provider_id=None)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Plugin 1개" in captured.out
    assert "Provider 설명 0개" in captured.out
