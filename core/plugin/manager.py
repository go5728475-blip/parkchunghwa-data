"""Plugin lifecycle and execution manager."""

from __future__ import annotations

from typing import Any

from core.domain.ids import PluginId
from core.domain.models import AnalysisSection
from core.plugin.errors import PluginExecutionError, PluginNotFoundError
from core.plugin.interface import PluginInterface
from core.plugin.registry import PluginRegistry


class PluginManager:
    """Coordinates plugin initialization, execution, and health checks."""

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    def initialize_all(self) -> None:
        """Initialize all enabled plugins."""
        for plugin in self._registry.list_enabled():
            plugin.initialize()

    def shutdown_all(self) -> None:
        """Shut down all registered plugins."""
        for plugin in self._registry.list():
            plugin.shutdown()

    def execute(self, plugin_id: PluginId, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a plugin by id."""
        if not self._registry.exists(plugin_id):
            msg = f"Plugin not found: {plugin_id}"
            raise PluginNotFoundError(msg)

        plugin = self._registry.get(plugin_id)
        if not plugin.metadata().enabled:
            msg = f"Plugin is disabled: {plugin_id}"
            raise PluginExecutionError(msg)

        try:
            return plugin.execute(input_data)
        except PluginExecutionError:
            raise
        except Exception as exc:  # noqa: BLE001
            msg = f"Plugin execution failed: {plugin_id}"
            raise PluginExecutionError(msg) from exc

    def find_plugin_for_capability(self, capability: str) -> PluginInterface:
        """Return the first enabled plugin that supports the capability."""
        for plugin in self._registry.list_enabled():
            if capability in plugin.metadata().capabilities:
                return plugin
        msg = f"No plugin found for capability: {capability}"
        raise PluginNotFoundError(msg)

    def execute_by_capability(
        self,
        capability: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve and execute a plugin by capability."""
        plugin = self.find_plugin_for_capability(capability)
        return self.execute(plugin.metadata().plugin_id, input_data)

    def execute_analysis_section(
        self,
        capability: str,
        input_data: dict[str, Any],
    ) -> AnalysisSection:
        """Resolve and create an analysis section from a plugin by capability."""
        plugin = self.find_plugin_for_capability(capability)
        return plugin.create_analysis_section(input_data)

    def health_check_all(self) -> dict[str, bool]:
        """Run health checks for all registered plugins."""
        return {
            str(plugin.metadata().plugin_id): plugin.health_check()
            for plugin in self._registry.list()
        }
