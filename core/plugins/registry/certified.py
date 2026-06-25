"""Certified plugin registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.registry.audit import RegistryAuditLogger, get_default_audit_logger


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, kw_only=True)
class CertifiedPluginRecord:
    """Registry entry for a certified plugin."""

    plugin_id: str
    version: str
    compatibility_level: PluginCompatibilityLevel
    certified: bool
    warnings: tuple[str, ...] = ()
    checks: tuple[str, ...] = ()
    certified_at: datetime = field(default_factory=_utc_now)


class CertifiedPluginRegistry:
    """Tracks certified plugin records."""

    def __init__(
        self,
        store: object | None = None,
        audit_logger: RegistryAuditLogger | None = None,
    ) -> None:
        self._store = store
        self._audit_logger = audit_logger or get_default_audit_logger()
        self._records: dict[str, CertifiedPluginRecord] = {}
        if store is not None:
            for record in store.load_all():
                self._records[record.plugin_id] = record

    def register(self, record: CertifiedPluginRecord) -> None:
        existing = self._records.get(record.plugin_id)
        self._records[record.plugin_id] = record
        if self._store is not None:
            self._store.save(record)
        if existing is None:
            self._audit_logger.record_register(record.plugin_id, record.version)
        else:
            self._audit_logger.record_update(record.plugin_id, record.version)

    def delete(self, plugin_id: str) -> None:
        existing = self._records.pop(plugin_id, None)
        if self._store is not None:
            self._store.delete(plugin_id)
        version = existing.version if existing is not None else "0.0.0"
        self._audit_logger.record_unregister(plugin_id, version)

    def get(self, plugin_id: str) -> CertifiedPluginRecord | None:
        return self._records.get(plugin_id)

    def list_all(self) -> tuple[CertifiedPluginRecord, ...]:
        return tuple(self._records[plugin_id] for plugin_id in sorted(self._records))

    def is_certified(self, plugin_id: str) -> bool:
        record = self._records.get(plugin_id)
        if record is None:
            return False
        return record.certified is True
