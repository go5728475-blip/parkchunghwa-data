"""Tests for explain-analysis CLI command."""

from __future__ import annotations

from core.cli.main import explain_analysis


def test_cli_explain_analysis_output(capsys) -> None:
    exit_code = explain_analysis(
        capability="wealth.analysis",
        provider_id="openai.stub",
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Explainable Analysis" in captured.out
    assert "Section: [PLUGIN]" in captured.out
    assert "Section: [PROVIDER]" in captured.out
    assert "Confidence:" in captured.out
    assert "Reasoning:" in captured.out
    assert "Evidence:" in captured.out
    assert "Trace:" in captured.out
    assert "PLUGIN" in captured.out
    assert "PROVIDER" in captured.out
    assert "Enriched from:" in captured.out
