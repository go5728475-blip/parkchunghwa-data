"""Plugin certification interfaces."""

from __future__ import annotations

from typing import Protocol

from core.plugins.certification.result import PluginCertificationResult


class PluginCertificationCheck(Protocol):
    """Contract for a single plugin certification check."""

    @property
    def name(self) -> str:
        """Return the check identifier."""

    def check(self, plugin: object) -> PluginCertificationResult:
        """Run the check against a plugin instance."""
