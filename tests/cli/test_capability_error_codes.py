"""Tests for CLI capability canonical error codes and suggestions."""

from __future__ import annotations

from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.configuration import EngineConfiguration
from core.cli.main import _failure_suggestion, run_analysis
from core.common.error_codes import ErrorCode


def test_cli_run_analysis_missing_capability_uses_canonical_code(capsys) -> None:
    exit_code = run_analysis(capability="missing.capability")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert ErrorCode.CAPABILITY_NOT_FOUND in captured.out
    assert ErrorCode.ENGINE_RUN_FAILED not in captured.out
    assert "suggestion: python -m core.cli.main list-capabilities" in captured.out


def test_failure_suggestion_capability_codes() -> None:
    assert (
        _failure_suggestion(ErrorCode.CAPABILITY_NOT_FOUND)
        == "python -m core.cli.main list-capabilities"
    )
    assert (
        _failure_suggestion(ErrorCode.CAPABILITY_DISABLED)
        == "python -m core.cli.main list-capabilities"
    )
    assert (
        _failure_suggestion(ErrorCode.CAPABILITY_NOT_SUPPORTED)
        == "python -m core.cli.main list-capabilities"
    )


def test_cli_run_analysis_unsupported_capability_suggestion(
    capsys,
    monkeypatch,
) -> None:
    class _ConfiguredBootstrap:
        def __init__(self, configuration: EngineConfiguration | None = None) -> None:
            self._configuration = configuration or EngineConfiguration(
                supported_capabilities=("stub.analysis",),
            )

        def build(self) -> Bootstrap:
            return Bootstrap(self._configuration).build()

    monkeypatch.setattr("core.cli.main.Bootstrap", _ConfiguredBootstrap)

    exit_code = run_analysis(capability="wealth.analysis")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert ErrorCode.CAPABILITY_NOT_SUPPORTED in captured.out
    assert ErrorCode.ENGINE_RUN_FAILED not in captured.out
    assert "suggestion: python -m core.cli.main list-capabilities" in captured.out
