"""Instance-based plugin loader."""

from __future__ import annotations

from core.domain.ids import PluginId
from core.plugin.interface import PluginInterface
from core.plugin.registry import PluginRegistry


class PluginLoader:
    """Loads plugin instances into the registry."""

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry

    def load_from_instance(self, plugin: PluginInterface) -> PluginId:
        """Register a plugin instance without initializing it."""
        self._registry.register(plugin)
        return plugin.metadata().plugin_id

    def unload(self, plugin_id: PluginId) -> None:
        """Shut down and unregister a plugin."""
        plugin = self._registry.get(plugin_id)
        plugin.shutdown()
        self._registry.unregister(plugin_id)
