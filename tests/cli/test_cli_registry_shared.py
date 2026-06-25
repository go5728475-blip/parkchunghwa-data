"""Tests for shared certified plugin registry across CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.bootstrap.bootstrap import Bootstrap
from core.cli.main import list_modules, module_info, register_certified
from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.registry.certified import CertifiedPluginRecord
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


def test_cli_registry_singleton(capsys) -> None:
    bootstrap = Bootstrap().build()
    first = bootstrap.certified_plugin_registry()

    register_certified(str(HEALTH_PLUGIN_DIR))
    capsys.readouterr()

    second_bootstrap = Bootstrap().build()
    second = second_bootstrap.certified_plugin_registry()

    assert first is not second
    assert second.get("health") is not None
    assert second.get("health").certified is True


def test_module_info_shows_certified_status(capsys) -> None:
    bootstrap = Bootstrap().build()
    registry = bootstrap.certified_plugin_registry()
    registry.register(
        CertifiedPluginRecord(
            plugin_id="wealth",
            version="0.1.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )

    exit_code = module_info(
        "wealth",
        module_registry=bootstrap.module_registry(),
        certified_registry=registry,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Certified:   yes" in captured.out
    assert "Compatibility: COMPATIBLE" in captured.out


def test_module_info_shows_unknown_for_unregistered_module(capsys) -> None:
    bootstrap = Bootstrap().build()

    exit_code = module_info(
        "wealth",
        module_registry=bootstrap.module_registry(),
        certified_registry=bootstrap.certified_plugin_registry(),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Certified:   no" in captured.out
    assert "Compatibility: UNKNOWN" in captured.out


def test_list_modules_shows_certified_columns(capsys) -> None:
    bootstrap = Bootstrap().build()
    registry = bootstrap.certified_plugin_registry()
    registry.register(
        CertifiedPluginRecord(
            plugin_id="wealth",
            version="0.1.0",
            compatibility_level=PluginCompatibilityLevel.PARTIAL,
            certified=True,
        ),
    )

    exit_code = list_modules(
        module_registry=bootstrap.module_registry(),
        certified_registry=registry,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "certified=yes" in captured.out
    assert "compatibility=PARTIAL" in captured.out


def test_list_modules_shows_unknown_compatibility(capsys) -> None:
    bootstrap = Bootstrap().build()

    exit_code = list_modules(
        module_registry=bootstrap.module_registry(),
        certified_registry=bootstrap.certified_plugin_registry(),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "certified=no" in captured.out
    assert "compatibility=UNKNOWN" in captured.out
