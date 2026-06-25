"""Certified plugin registry persistence interface."""

from __future__ import annotations

from typing import Protocol

from core.plugins.registry.certified import CertifiedPluginRecord


class CertifiedPluginRegistryStore(Protocol):
    """Persistence backend for certified plugin records."""

    def save(self, record: CertifiedPluginRecord) -> None:
        """Persist a certified plugin record."""

    def load(self, plugin_id: str) -> CertifiedPluginRecord | None:
        """Load a single certified plugin record."""

    def load_all(self) -> tuple[CertifiedPluginRecord, ...]:
        """Load all certified plugin records."""

    def delete(self, plugin_id: str) -> None:
        """Remove a certified plugin record."""
