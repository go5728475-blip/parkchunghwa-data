"""Tests for CLI default certified plugin registry wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.bootstrap.bootstrap import Bootstrap
from core.cli.main import (
    is_certified,
    list_certified,
    load_module,
    register_certified,
    unregister_certified,
)
from core.plugins.registry.paths import get_default_certified_registry_path
from core.plugins.registry.provider import reset_default_registry


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
HEALTH_PLUGIN_DIR = FIXTURES_DIR / "health_plugin"


@pytest.fixture(autouse=True)
def _isolated_default_registry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("MASTER_ENGINE_CERTIFIED_REGISTRY", raising=False)
    monkeypatch.chdir(tmp_path)
    reset_default_registry()


def test_register_certified_without_registry_path(capsys) -> None:
    exit_code = register_certified(str(HEALTH_PLUGIN_DIR))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Registry Path:" in captured.out
    assert get_default_certified_registry_path().exists()


def test_list_certified_without_registry_path(capsys) -> None:
    register_certified(str(HEALTH_PLUGIN_DIR))
    capsys.readouterr()

    exit_code = list_certified()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Plugin ID:     health" in captured.out
    assert "Compatibility: COMPATIBLE" in captured.out


def test_is_certified_without_registry_path(capsys) -> None:
    register_certified(str(HEALTH_PLUGIN_DIR))
    capsys.readouterr()

    exit_code = is_certified("health")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Plugin Certified" in captured.out


def test_load_module_certified_only_without_registry_path(capsys) -> None:
    bootstrap = Bootstrap().build()

    exit_code = load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Registry Path:" in captured.out
    assert get_default_certified_registry_path().exists()
    assert bootstrap.module_registry().exists("health")


def test_unregister_certified_without_registry_path(capsys) -> None:
    register_certified(str(HEALTH_PLUGIN_DIR))
    capsys.readouterr()

    exit_code = unregister_certified("health")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Certified Plugin Unregistered" in captured.out

    assert is_certified("health") == 1
    capsys.readouterr()


def test_default_registry_auto_created() -> None:
    registry_path = get_default_certified_registry_path()

    assert not registry_path.exists()

    register_certified(str(HEALTH_PLUGIN_DIR))

    assert registry_path.parent.is_dir()
    assert registry_path.exists()
