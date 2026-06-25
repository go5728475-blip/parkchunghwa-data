"""Plugin interface contract."""

from __future__ import annotations

from typing import Any, Protocol

from core.domain.models import AnalysisSection
from core.plugin.metadata import PluginMetadata


class PluginInterface(Protocol):
    """Contract for MASTER ENGINE plugins."""

    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""

    def initialize(self) -> None:
        """Prepare the plugin for execution."""

    def shutdown(self) -> None:
        """Release plugin resources."""

    def health_check(self) -> bool:
        """Return whether the plugin is healthy."""

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute plugin logic with the given input payload."""

    def create_analysis_section(self, input_data: dict[str, Any]) -> AnalysisSection:
        """Create a canonical analysis section from plugin execution."""
