"""Tests for certified plugin registry audit trail."""

from __future__ import annotations

from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.registry.audit import RegistryAuditLogger
from core.plugins.registry.certified import CertifiedPluginRecord, CertifiedPluginRegistry


def _record(*, plugin_id: str, version: str) -> CertifiedPluginRecord:
    return CertifiedPluginRecord(
        plugin_id=plugin_id,
        version=version,
        compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
        certified=True,
    )


def test_register_audit() -> None:
    audit_logger = RegistryAuditLogger()
    registry = CertifiedPluginRegistry(audit_logger=audit_logger)

    registry.register(_record(plugin_id="wealth", version="1.0.0"))

    entries = audit_logger.list_entries()
    assert len(entries) == 1
    assert entries[0].action == "register"
    assert entries[0].plugin_id == "wealth"
    assert entries[0].version == "1.0.0"
    assert entries[0].result == "success"


def test_unregister_audit() -> None:
    audit_logger = RegistryAuditLogger()
    registry = CertifiedPluginRegistry(audit_logger=audit_logger)
    registry.register(_record(plugin_id="career", version="0.1.0"))

    registry.delete("career")

    entries = audit_logger.list_entries()
    assert entries[-1].action == "unregister"
    assert entries[-1].plugin_id == "career"
    assert entries[-1].version == "0.1.0"


def test_update_audit() -> None:
    audit_logger = RegistryAuditLogger()
    registry = CertifiedPluginRegistry(audit_logger=audit_logger)
    registry.register(_record(plugin_id="health", version="1.0.0"))

    registry.register(_record(plugin_id="health", version="2.0.0"))

    entries = audit_logger.list_entries()
    assert entries[-1].action == "update"
    assert entries[-1].plugin_id == "health"
    assert entries[-1].version == "2.0.0"


def test_list_entries() -> None:
    audit_logger = RegistryAuditLogger()
    registry = CertifiedPluginRegistry(audit_logger=audit_logger)
    registry.register(_record(plugin_id="study", version="0.1.0"))
    registry.register(_record(plugin_id="study", version="0.2.0"))
    registry.delete("study")

    entries = audit_logger.list_entries()

    assert [entry.action for entry in entries] == ["register", "update", "unregister"]
    assert len(entries) == 3
