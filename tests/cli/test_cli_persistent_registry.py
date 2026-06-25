"""Tests for persistent certified plugin registry CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.cli.main import is_certified, list_certified, register_certified
from core.plugins.registry.factory import create_json_certified_plugin_registry


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
HEALTH_PLUGIN_DIR = FIXTURES_DIR / "health_plugin"


def test_register_certified_registry_path_persists_record(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "certified.json"

    exit_code = register_certified(
        str(HEALTH_PLUGIN_DIR),
        registry_path=str(registry_path),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert registry_path.exists()
    assert "Registry Path:" in captured.out

    registry = create_json_certified_plugin_registry(registry_path)
    record = registry.get("health")
    assert record is not None
    assert record.certified is True


def test_list_certified_shows_persisted_plugin(tmp_path: Path, capsys) -> None:
    registry_path = tmp_path / "certified.json"
    register_certified(str(HEALTH_PLUGIN_DIR), registry_path=str(registry_path))
    capsys.readouterr()

    exit_code = list_certified(registry_path=str(registry_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Certified Plugins" in captured.out
    assert "Plugin ID:     health" in captured.out
    assert "Compatibility: COMPATIBLE" in captured.out
    assert "Certified:     True" in captured.out


def test_is_certified_returns_success_for_certified_plugin(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "certified.json"
    register_certified(str(HEALTH_PLUGIN_DIR), registry_path=str(registry_path))
    capsys.readouterr()

    exit_code = is_certified("health", registry_path=str(registry_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Plugin Certified" in captured.out
    assert "Plugin ID:           health" in captured.out


def test_is_certified_returns_failure_for_missing_plugin(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "certified.json"

    exit_code = is_certified("missing", registry_path=str(registry_path))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "[MASTER ENGINE] Plugin Not Certified" in captured.out
    assert "Plugin ID: missing" in captured.out


def test_list_certified_empty_registry_succeeds(tmp_path: Path, capsys) -> None:
    registry_path = tmp_path / "certified.json"

    exit_code = list_certified(registry_path=str(registry_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Certified Plugins" in captured.out
    assert "No certified plugins." in captured.out


def test_is_certified_returns_failure_for_uncertified_record(
    tmp_path: Path,
    capsys,
) -> None:
    from core.plugins.certification.levels import PluginCompatibilityLevel
    from core.plugins.registry.certified import CertifiedPluginRecord

    registry_path = tmp_path / "certified.json"
    registry = create_json_certified_plugin_registry(registry_path)
    registry.register(
        CertifiedPluginRecord(
            plugin_id="broken",
            version="0.1.0",
            compatibility_level=PluginCompatibilityLevel.INCOMPATIBLE,
            certified=False,
        ),
    )

    exit_code = is_certified("broken", registry_path=str(registry_path))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "[MASTER ENGINE] Plugin Not Certified" in captured.out
