"""Tests for certified plugin load pipeline CLI integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.bootstrap.bootstrap import Bootstrap
from core.cli.main import load_module, register_certified, unregister_certified
from core.plugins.registry.factory import create_json_certified_plugin_registry


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
HEALTH_PLUGIN_DIR = FIXTURES_DIR / "health_plugin"


def test_load_module_certified_only_registry_path_persists_certification_record(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "certified.json"
    bootstrap = Bootstrap().build()

    exit_code = load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
        registry_path=str(registry_path),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert bootstrap.module_registry().exists("health")

    registry = create_json_certified_plugin_registry(registry_path)
    record = registry.get("health")
    assert record is not None
    assert record.certified is True
    assert "Registry Path:" in captured.out


def test_load_module_require_registered_unregistered_fails(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "certified.json"
    bootstrap = Bootstrap().build()

    exit_code = load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
        registry_path=str(registry_path),
        require_registered=True,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "[MASTER ENGINE] LoadModule failed" in captured.out
    assert "not registered as certified" in captured.out
    assert not bootstrap.module_registry().exists("health")


def test_load_module_require_registered_after_register_certified_succeeds(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "certified.json"
    bootstrap = Bootstrap().build()

    register_exit = register_certified(
        str(HEALTH_PLUGIN_DIR),
        registry_path=str(registry_path),
    )
    capsys.readouterr()
    assert register_exit == 0

    exit_code = load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
        registry_path=str(registry_path),
        require_registered=True,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Module Loaded" in captured.out
    assert "Registered Required: True" in captured.out
    assert bootstrap.module_registry().exists("health")


def test_load_module_require_registered_without_certified_only_fails(capsys) -> None:
    bootstrap = Bootstrap().build()

    exit_code = load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
        require_registered=True,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--require-registered requires --certified-only" in captured.out


def test_unregister_certified_deletes_record(tmp_path: Path, capsys) -> None:
    registry_path = tmp_path / "certified.json"
    register_certified(str(HEALTH_PLUGIN_DIR), registry_path=str(registry_path))
    capsys.readouterr()

    exit_code = unregister_certified("health", registry_path=str(registry_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Certified Plugin Unregistered" in captured.out

    registry = create_json_certified_plugin_registry(registry_path)
    assert registry.get("health") is None


def test_unregister_certified_missing_plugin_id_succeeds(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "certified.json"

    exit_code = unregister_certified("missing", registry_path=str(registry_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Certified Plugin Unregistered" in captured.out
    assert "Plugin ID:     missing" in captured.out


def test_load_module_output_includes_registry_path(tmp_path: Path, capsys) -> None:
    registry_path = tmp_path / "certified.json"
    bootstrap = Bootstrap().build()

    load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
        registry_path=str(registry_path),
    )
    captured = capsys.readouterr()

    assert f"Registry Path:       {registry_path}" in captured.out


def test_load_module_output_includes_registered_required(capsys) -> None:
    bootstrap = Bootstrap().build()

    load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
    )
    captured = capsys.readouterr()

    assert "Registered Required: False" in captured.out
