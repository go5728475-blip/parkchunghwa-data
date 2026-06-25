"""Tests for runtime registry bridge."""

from __future__ import annotations

from core.certification.models import CertificationDecision, DecisionStatus
from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.plugin_registry import CertificationPluginRegistry
from core.plugins.registry.certified import CertifiedPluginRecord, CertifiedPluginRegistry
from core.runtime.registry_bridge import RuntimeRegistryBridge


def test_get_runtime_plugins() -> None:
    runtime_registry = CertificationPluginRegistry()
    runtime_registry.set_decision(
        "health",
        CertificationDecision(status=DecisionStatus.PASS),
    )
    bridge = RuntimeRegistryBridge(runtime_registry)

    assert bridge.get_runtime_plugins() == ("health",)


def test_get_certified_plugins() -> None:
    certified = CertifiedPluginRegistry()
    certified.register(
        CertifiedPluginRecord(
            plugin_id="health",
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )
    bridge = RuntimeRegistryBridge(CertificationPluginRegistry(), certified)

    assert bridge.get_certified_plugins() == ("health",)


def test_get_plugin_status() -> None:
    runtime_registry = CertificationPluginRegistry()
    runtime_registry.set_decision(
        "warning",
        CertificationDecision(
            status=DecisionStatus.WARN,
            recommendations=("provider warning",),
        ),
        warnings=("provider warning",),
    )
    bridge = RuntimeRegistryBridge(runtime_registry)

    status = bridge.get_plugin_status("warning")

    assert status.runtime_status == "WARN"
    assert status.registered is True


def test_is_certified_from_certified_registry() -> None:
    certified = CertifiedPluginRegistry()
    certified.register(
        CertifiedPluginRecord(
            plugin_id="wealth",
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )
    bridge = RuntimeRegistryBridge(CertificationPluginRegistry(), certified)

    assert bridge.is_certified("wealth") is True
    assert bridge.is_certified("missing") is False


def test_certification_summary() -> None:
    runtime_registry = CertificationPluginRegistry()
    runtime_registry.set_decision("pass", CertificationDecision(status=DecisionStatus.PASS))
    runtime_registry.set_decision("warn", CertificationDecision(status=DecisionStatus.WARN))
    runtime_registry.set_decision("fail", CertificationDecision(status=DecisionStatus.FAIL))
    bridge = RuntimeRegistryBridge(runtime_registry)

    summary = bridge.certification_summary()

    assert summary["runtime_plugins"] == ("fail", "pass", "warn")
    assert summary["warning_plugins"] == ("warn",)
    assert summary["blocked_plugins"] == ("fail",)
