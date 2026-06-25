"""Tests for dynamic module CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.bootstrap.bootstrap import Bootstrap
from core.cli.main import load_module, reload_module, unload_module


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
HEALTH_PLUGIN_DIR = FIXTURES_DIR / "health_plugin"
STUDY_PLUGIN_DIR = FIXTURES_DIR / "study_plugin"


def test_cli_load_module_registers_dynamic_module(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Module Loaded" in captured.out
    assert "Module Name: health" in captured.out
    assert bootstrap.module_registry().exists("health")


def test_cli_unload_module_removes_dynamic_module(capsys) -> None:
    bootstrap = Bootstrap().build()
    manager = bootstrap.loader_manager()
    manager.load(str(HEALTH_PLUGIN_DIR))

    exit_code = unload_module("health", loader_manager=manager)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Module Unloaded" in captured.out
    assert not bootstrap.module_registry().exists("health")


def test_cli_reload_module_reloads_dynamic_module(capsys) -> None:
    bootstrap = Bootstrap().build()
    manager = bootstrap.loader_manager()
    manager.load(str(STUDY_PLUGIN_DIR))

    exit_code = reload_module("study", loader_manager=manager)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Module Reloaded" in captured.out
    assert bootstrap.module_registry().exists("study")


def test_cli_load_module_failure_returns_error(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = load_module(
        "/missing/plugin",
        loader_manager=bootstrap.loader_manager(),
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "[MASTER ENGINE] LoadModule failed" in captured.out


def test_builtin_and_dynamic_modules_listed_together(capsys) -> None:
    from core.cli.main import list_modules

    bootstrap = Bootstrap().build()
    bootstrap.loader_manager().load(str(HEALTH_PLUGIN_DIR))

    exit_code = list_modules(module_registry=bootstrap.module_registry())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "wealth" in captured.out
    assert "health" in captured.out
