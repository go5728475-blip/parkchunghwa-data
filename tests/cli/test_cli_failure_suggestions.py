"""Tests for CLI failure suggestions."""

from __future__ import annotations

from core.cli.main import generate_text, run_analysis
from core.common.error_codes import ErrorCode


def test_cli_generate_text_missing_provider_suggestion(capsys) -> None:
    exit_code = generate_text("missing.provider", "hello")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "PROVIDER_NOT_FOUND" in captured.out
    assert "suggestion: python -m core.cli.main list-providers" in captured.out


def test_cli_run_analysis_missing_provider_suggestion(capsys) -> None:
    exit_code = run_analysis(
        capability="stub.analysis",
        provider_id="missing.provider",
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "PROVIDER_NOT_FOUND" in captured.out
    assert "suggestion: python -m core.cli.main list-providers" in captured.out


def test_cli_run_analysis_missing_capability_suggestion(capsys) -> None:
    exit_code = run_analysis(capability="missing.capability")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert ErrorCode.CAPABILITY_NOT_FOUND in captured.out
    assert "suggestion: python -m core.cli.main list-capabilities" in captured.out
