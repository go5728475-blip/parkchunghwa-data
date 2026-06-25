"""Certified plugin registry audit trail."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, kw_only=True)
class RegistryAuditEntry:
    """Audit record for certified plugin registry changes."""

    timestamp: str
    action: str
    plugin_id: str
    version: str
    result: str


class RegistryAuditLogger:
    """Audit logger for certified plugin registry changes."""

    def __init__(self, store: object | None = None) -> None:
        self._store = store
        self._entries: list[RegistryAuditEntry] = []
        if store is not None:
            self._entries.extend(store.load_all())

    def record_register(
        self,
        plugin_id: str,
        version: str,
        *,
        result: str = "success",
    ) -> RegistryAuditEntry:
        return self._record("register", plugin_id, version, result)

    def record_unregister(
        self,
        plugin_id: str,
        version: str,
        *,
        result: str = "success",
    ) -> RegistryAuditEntry:
        return self._record("unregister", plugin_id, version, result)

    def record_update(
        self,
        plugin_id: str,
        version: str,
        *,
        result: str = "success",
    ) -> RegistryAuditEntry:
        return self._record("update", plugin_id, version, result)

    def list_entries(self) -> tuple[RegistryAuditEntry, ...]:
        return tuple(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        if self._store is not None:
            self._store.clear()

    def _record(
        self,
        action: str,
        plugin_id: str,
        version: str,
        result: str,
    ) -> RegistryAuditEntry:
        entry = RegistryAuditEntry(
            timestamp=datetime.now(UTC).isoformat(),
            action=action,
            plugin_id=plugin_id,
            version=version,
            result=result,
        )
        self._entries.append(entry)
        if self._store is not None:
            self._store.append(entry)
        return entry


_default_audit_logger: RegistryAuditLogger | None = None


def get_default_audit_logger() -> RegistryAuditLogger:
    """Return the process-wide default registry audit logger."""
    global _default_audit_logger
    if _default_audit_logger is None:
        from core.plugins.registry.audit_json_store import JsonRegistryAuditStore
        from core.plugins.registry.paths import ensure_default_audit_file

        store = JsonRegistryAuditStore(ensure_default_audit_file())
        _default_audit_logger = RegistryAuditLogger(store=store)
    return _default_audit_logger


def reset_default_audit_logger() -> None:
    """Reset the cached default audit logger instance."""
    global _default_audit_logger
    _default_audit_logger = None
