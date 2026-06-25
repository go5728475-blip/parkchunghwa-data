"""Tests for certified plugin registry."""

from __future__ import annotations

from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.certification.result import PluginCertificationResult
from core.plugins.registry.certified import CertifiedPluginRecord, CertifiedPluginRegistry


def _record(
    *,
    plugin_id: str,
    version: str,
    compatibility_level: PluginCompatibilityLevel,
    certified: bool,
) -> CertifiedPluginRecord:
    return CertifiedPluginRecord(
        plugin_id=plugin_id,
        version=version,
        compatibility_level=compatibility_level,
        certified=certified,
    )


def test_certified_record_creation() -> None:
    record = _record(
        plugin_id="wealth",
        version="1.0.0",
        compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
        certified=True,
    )

    assert record.plugin_id == "wealth"
    assert record.certified is True


def test_registry_register_and_get() -> None:
    registry = CertifiedPluginRegistry()
    record = _record(
        plugin_id="career",
        version="0.1.0",
        compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
        certified=True,
    )

    registry.register(record)

    assert registry.get("career") == record


def test_registry_list_all_returns_sorted_records() -> None:
    registry = CertifiedPluginRegistry()
    registry.register(
        _record(
            plugin_id="wealth",
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )
    registry.register(
        _record(
            plugin_id="career",
            version="0.1.0",
            compatibility_level=PluginCompatibilityLevel.PARTIAL,
            certified=True,
        ),
    )

    records = registry.list_all()

    assert [record.plugin_id for record in records] == ["career", "wealth"]


def test_is_certified_true_only_for_certified_records() -> None:
    registry = CertifiedPluginRegistry()
    registry.register(
        _record(
            plugin_id="health",
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )

    assert registry.is_certified("health") is True
    assert registry.is_certified("missing") is False


def test_failed_record_is_not_certified() -> None:
    registry = CertifiedPluginRegistry()
    registry.register(
        CertifiedPluginRecord(
            plugin_id="broken",
            version="0.1.0",
            compatibility_level=PluginCompatibilityLevel.INCOMPATIBLE,
            certified=False,
        ),
    )

    assert registry.is_certified("broken") is False


def test_same_plugin_id_re_register_replaces_record() -> None:
    registry = CertifiedPluginRegistry()
    first = _record(
        plugin_id="study",
        version="0.1.0",
        compatibility_level=PluginCompatibilityLevel.PARTIAL,
        certified=True,
    )
    second = _record(
        plugin_id="study",
        version="0.2.0",
        compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
        certified=True,
    )

    registry.register(first)
    registry.register(second)

    assert registry.get("study") == second
    assert registry.list_all() == (second,)


def test_registry_record_stores_warnings_and_checks() -> None:
    registry = CertifiedPluginRegistry()
    record = CertifiedPluginRecord(
        plugin_id="relationship",
        version="1.0.0",
        compatibility_level=PluginCompatibilityLevel.PARTIAL,
        certified=True,
        warnings=("provider warning",),
        checks=("manifest_required", "provider_independence"),
    )

    registry.register(record)

    stored = registry.get("relationship")
    assert stored is not None
    assert stored.warnings == ("provider warning",)
    assert stored.checks == ("manifest_required", "provider_independence")
