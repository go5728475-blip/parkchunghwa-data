"""Tests for default certified plugin registry provider."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.bootstrap.factory import create_certified_plugin_registry
from core.plugins.registry.factory import create_json_certified_plugin_registry
from core.plugins.registry.paths import (
    ensure_default_registry_directory,
    ensure_default_registry_file,
    get_default_certified_registry_path,
)
from core.plugins.registry.provider import get_default_registry, reset_default_registry
from core.plugins.registry.certified import CertifiedPluginRecord
from core.plugins.certification.levels import PluginCompatibilityLevel


@pytest.fixture(autouse=True)
def _isolated_default_registry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("MASTER_ENGINE_CERTIFIED_REGISTRY", raising=False)
    monkeypatch.chdir(tmp_path)
    reset_default_registry()


def test_default_provider_singleton() -> None:
    first = get_default_registry()
    second = get_default_registry()

    assert first is second


def test_default_provider_loads_json_registry() -> None:
    registry_path = ensure_default_registry_file()
    store_registry = create_json_certified_plugin_registry(registry_path)
    store_registry.register(
        CertifiedPluginRecord(
            plugin_id="wealth",
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )
    reset_default_registry()

    registry = get_default_registry()

    assert registry.get("wealth") is not None
    assert registry.get("wealth").certified is True


def test_ensure_directory_creates_folder(tmp_path: Path) -> None:
    directory = ensure_default_registry_directory()

    assert directory == tmp_path / ".master_engine"
    assert directory.is_dir()


def test_ensure_file_creates_json(tmp_path: Path) -> None:
    registry_path = ensure_default_registry_file()

    assert registry_path == tmp_path / ".master_engine" / "certified_plugins.json"
    assert registry_path.exists()
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert data == {"plugins": {}}


def test_default_provider_survives_restart(tmp_path: Path) -> None:
    first = get_default_registry()
    first.register(
        CertifiedPluginRecord(
            plugin_id="career",
            version="0.1.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )
    reset_default_registry()

    second = get_default_registry()

    assert second.get("career") is not None
    assert second.get("career").version == "0.1.0"


def test_bootstrap_create_certified_plugin_registry_uses_default_json(tmp_path: Path) -> None:
    registry = create_certified_plugin_registry()
    registry.register(
        CertifiedPluginRecord(
            plugin_id="health",
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )

    registry_path = get_default_certified_registry_path()
    reloaded = create_json_certified_plugin_registry(registry_path)

    assert reloaded.get("health") is not None
