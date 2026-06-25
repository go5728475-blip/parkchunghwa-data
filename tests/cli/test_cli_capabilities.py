"""Tests for CLI capability listing."""

from __future__ import annotations

from core.cli.main import list_capabilities


def test_cli_list_capabilities_success(capsys) -> None:
    exit_code = list_capabilities()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Registered capabilities" in captured.out
    assert "stub.analysis" in captured.out
    assert "wealth.analysis" in captured.out
    assert "master_lock.analysis" in captured.out
    assert "career.analysis" in captured.out
    assert "relationship.analysis" in captured.out
