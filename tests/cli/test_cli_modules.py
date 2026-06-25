"""Tests for module CLI commands."""

from __future__ import annotations

from core.bootstrap.bootstrap import Bootstrap
from core.cli.main import list_modules, module_info


def test_cli_list_modules_lists_builtin_modules(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = list_modules(module_registry=bootstrap.module_registry())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Registered Modules" in captured.out
    assert "wealth" in captured.out
    assert "career" in captured.out
    assert "relationship" in captured.out
    assert "master_lock" in captured.out
    assert "loaded=yes" in captured.out


def test_cli_module_info_shows_module_details(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = module_info("wealth", module_registry=bootstrap.module_registry())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Module Info" in captured.out
    assert "Module Name: wealth" in captured.out
    assert "Version:     0.1.0" in captured.out
    assert "wealth.analysis" in captured.out
    assert "Loaded:      yes" in captured.out


def test_cli_module_info_missing_module_returns_error(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = module_info("missing", module_registry=bootstrap.module_registry())
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Module not found" in captured.out


def test_bootstrap_registers_module_registry() -> None:
    bootstrap = Bootstrap().build()

    assert bootstrap.container().exists("module_registry")
    assert bootstrap.module_registry().exists("wealth")
