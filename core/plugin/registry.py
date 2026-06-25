"""In-memory plugin registry."""

from __future__ import annotations

from core.domain.ids import PluginId
from core.plugin.errors import DuplicatePluginError, PluginNotFoundError
from core.plugin.interface import PluginInterface


class PluginRegistry:
    """Stores plugin instances keyed by plugin id."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginInterface] = {}

    def register(self, plugin: PluginInterface) -> None:
        """Register a plugin instance."""
        plugin_id = str(plugin.metadata().plugin_id)
        if plugin_id in self._plugins:
            msg = f"Plugin already registered: {plugin_id}"
            raise DuplicatePluginError(msg)
        self._plugins[plugin_id] = plugin

    def unregister(self, plugin_id: PluginId) -> None:
        """Remove a plugin by id."""
        key = str(plugin_id)
        if key not in self._plugins:
            msg = f"Plugin not found: {plugin_id}"
            raise PluginNotFoundError(msg)
        del self._plugins[key]

    def get(self, plugin_id: PluginId) -> PluginInterface:
        """Return a registered plugin."""
        plugin = self._plugins.get(str(plugin_id))
        if plugin is None:
            msg = f"Plugin not found: {plugin_id}"
            raise PluginNotFoundError(msg)
        return plugin

    def list(self) -> list[PluginInterface]:
        """Return all registered plugins."""
        return list(self._plugins.values())

    def list_enabled(self) -> list[PluginInterface]:
        """Return registered plugins marked as enabled."""
        return [plugin for plugin in self._plugins.values() if plugin.metadata().enabled]

    def exists(self, plugin_id: PluginId) -> bool:
        """Return whether a plugin id is registered."""
        return str(plugin_id) in self._plugins
