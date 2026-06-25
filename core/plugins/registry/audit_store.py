"""Registry audit persistence interface."""

from __future__ import annotations

from typing import Protocol

from core.plugins.registry.audit import RegistryAuditEntry


class RegistryAuditStore(Protocol):
    """Persistence backend for registry audit entries."""

    def append(self, entry: RegistryAuditEntry) -> None:
        """Persist a single audit entry."""

    def load_all(self) -> tuple[RegistryAuditEntry, ...]:
        """Load all audit entries."""

    def clear(self) -> None:
        """Remove all persisted audit entries."""
