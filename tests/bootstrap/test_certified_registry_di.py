"""Tests for certified plugin registry DI wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.bootstrap.bootstrap import Bootstrap, CONTAINER_KEY_CERTIFIED_PLUGIN_REGISTRY
from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.certification.load_gate import certify_plugin_before_load
from core.plugins.registry.certified import CertifiedPluginRecord
from core.plugins.registry.provider import reset_default_registry
from core.plugins.registry.resolver import resolve_certified_registry
from tests.plugins.test_plugin_certification import _ValidPlugin


@pytest.fixture(autouse=True)
def _isolated_default_registry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("MASTER_ENGINE_CERTIFIED_REGISTRY", raising=False)
    monkeypatch.chdir(tmp_path)
    reset_default_registry()


def test_container_certified_registry_singleton() -> None:
    bootstrap = Bootstrap().build()
    container = bootstrap.container()

    first = container.resolve(CONTAINER_KEY_CERTIFIED_PLUGIN_REGISTRY)
    second = container.resolve(CONTAINER_KEY_CERTIFIED_PLUGIN_REGISTRY)

    assert first is second


def test_resolve_registry_from_container() -> None:
    bootstrap = Bootstrap().build()

    registry = resolve_certified_registry(bootstrap.container())

    assert registry is bootstrap.certified_plugin_registry()


def test_resolve_registry_fallback_default() -> None:
    registry = resolve_certified_registry()

    assert registry is not None
    assert hasattr(registry, "register")


def test_load_gate_uses_container_registry() -> None:
    bootstrap = Bootstrap().build()
    registry = bootstrap.certified_plugin_registry()
    registry.register(
        CertifiedPluginRecord(
            plugin_id="wealth",
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )

    record = certify_plugin_before_load(
        _ValidPlugin(),
        container=bootstrap.container(),
    )

    assert record.plugin_id == "wealth"
    assert registry.get("wealth") is not None
