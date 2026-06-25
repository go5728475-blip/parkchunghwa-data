"""Tests for plugin certification gate."""

from __future__ import annotations

import pytest

from core.plugins.certification.gate import CertificationGate
from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.certification.load_gate import (
    PluginCertificationError,
    certify_plugin_before_load,
)
from core.plugins.registry.certified import CertifiedPluginRegistry
from tests.plugins.test_plugin_certification import (
    _IncompatibleSdkPlugin,
    _OpenAIReferencedPlugin,
    _ValidPlugin,
)


def test_strict_gate_allows_valid_plugin() -> None:
    gate = CertificationGate(strict=True)

    assert gate.allow(_ValidPlugin()) is True


def test_strict_gate_blocks_invalid_plugin() -> None:
    gate = CertificationGate(strict=True)

    assert gate.allow(_IncompatibleSdkPlugin()) is False


def test_non_strict_gate_allows_invalid_plugin_but_records_uncertified() -> None:
    registry = CertifiedPluginRegistry()
    gate = CertificationGate(registry=registry, strict=False)
    plugin = _IncompatibleSdkPlugin()

    assert gate.allow(plugin) is True

    record = gate.certify_and_register(plugin)

    assert record.certified is False
    assert record.compatibility_level == PluginCompatibilityLevel.INCOMPATIBLE
    assert registry.get("health").certified is False


def test_warnings_only_plugin_allowed_as_partial() -> None:
    gate = CertificationGate(strict=True)
    plugin = _OpenAIReferencedPlugin()

    assert gate.allow(plugin) is True

    record = gate.certify_and_register(plugin)

    assert record.certified is True
    assert record.compatibility_level == PluginCompatibilityLevel.PARTIAL
    assert record.warnings


def test_certify_and_register_stores_record() -> None:
    registry = CertifiedPluginRegistry()
    gate = CertificationGate(registry=registry)

    record = gate.certify_and_register(_ValidPlugin())

    assert registry.get("wealth") == record
    assert record.certified is True
    assert record.compatibility_level == PluginCompatibilityLevel.COMPATIBLE


def test_certify_plugin_before_load_raises_on_failure() -> None:
    gate = CertificationGate(strict=True)

    with pytest.raises(PluginCertificationError) as exc_info:
        certify_plugin_before_load(_IncompatibleSdkPlugin(), gate)

    assert exc_info.value.result.plugin_id == "health"
    assert exc_info.value.result.errors


def test_certify_plugin_before_load_returns_record_on_success() -> None:
    registry = CertifiedPluginRegistry()
    gate = CertificationGate(registry=registry, strict=True)

    record = certify_plugin_before_load(_ValidPlugin(), gate)

    assert record.plugin_id == "wealth"
    assert record.certified is True
    assert registry.is_certified("wealth")
