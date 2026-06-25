"""Tests for certified plugin load pipeline."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.plugins.certification.gate import CertificationGate
from core.plugins.certification.load_gate import (
    PluginCertificationError,
    certify_plugin_before_load,
)
from core.plugins.registry.certified import CertifiedPluginRecord, CertifiedPluginRegistry
from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.registry.factory import create_json_certified_plugin_registry
from core.plugins.registry.paths import get_default_certified_registry_path
from tests.plugins.test_plugin_certification import _IncompatibleSdkPlugin, _ValidPlugin


def _registered_registry(plugin_id: str = "wealth") -> CertifiedPluginRegistry:
    registry = CertifiedPluginRegistry()
    registry.register(
        CertifiedPluginRecord(
            plugin_id=plugin_id,
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )
    return registry


def test_require_registered_false_keeps_existing_certification_success() -> None:
    registry = CertifiedPluginRegistry()
    gate = CertificationGate(registry=registry, strict=True)

    record = certify_plugin_before_load(
        _ValidPlugin(),
        gate,
        require_registered=False,
    )

    assert record.certified is True
    assert registry.is_certified("wealth")


def test_require_registered_true_registry_none_fails() -> None:
    gate = CertificationGate(strict=True)

    with pytest.raises(PluginCertificationError) as exc_info:
        certify_plugin_before_load(
            _ValidPlugin(),
            gate,
            require_registered=True,
            registry=None,
        )

    assert "certified plugin registry is required" in exc_info.value.result.errors[0]


def test_require_registered_true_unregistered_plugin_fails() -> None:
    registry = CertifiedPluginRegistry()
    gate = CertificationGate(registry=registry, strict=True)

    with pytest.raises(PluginCertificationError) as exc_info:
        certify_plugin_before_load(
            _ValidPlugin(),
            gate,
            require_registered=True,
            registry=registry,
        )

    assert "not registered as certified" in exc_info.value.result.errors[0]


def test_require_registered_true_registered_plugin_succeeds() -> None:
    registry = _registered_registry()
    gate = CertificationGate(registry=registry, strict=True)

    record = certify_plugin_before_load(
        _ValidPlugin(),
        gate,
        require_registered=True,
        registry=registry,
    )

    assert record.plugin_id == "wealth"
    assert registry.is_certified("wealth")


def test_certification_failure_fails_regardless_of_registry() -> None:
    registry = _registered_registry(plugin_id="health")
    gate = CertificationGate(registry=registry, strict=True)

    with pytest.raises(PluginCertificationError) as exc_info:
        certify_plugin_before_load(
            _IncompatibleSdkPlugin(),
            gate,
            require_registered=True,
            registry=registry,
        )

    assert exc_info.value.result.passed is False
    assert any("sdk_version" in error.lower() or "Incompatible" in error
               for error in exc_info.value.result.errors)


def test_default_registry_path_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "MASTER_ENGINE_CERTIFIED_REGISTRY",
        "/tmp/custom/certified_plugins.json",
    )

    assert get_default_certified_registry_path() == Path(
        "/tmp/custom/certified_plugins.json",
    )


def test_default_registry_path_falls_back_to_cwd_master_engine(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("MASTER_ENGINE_CERTIFIED_REGISTRY", raising=False)
    monkeypatch.chdir(tmp_path)

    assert get_default_certified_registry_path() == (
        tmp_path / ".master_engine" / "certified_plugins.json"
    )


def test_certified_only_with_registry_path_persists_record(tmp_path: Path) -> None:
    registry_path = tmp_path / "certified.json"
    registry = create_json_certified_plugin_registry(registry_path)
    registry.register(
        CertifiedPluginRecord(
            plugin_id="wealth",
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )

    gate = CertificationGate(registry=registry, strict=True)
    certify_plugin_before_load(
        _ValidPlugin(),
        gate,
        require_registered=True,
        registry=registry,
    )

    reloaded = create_json_certified_plugin_registry(registry_path)
    assert reloaded.is_certified("wealth")
