"""Tests for plugin loader."""

from __future__ import annotations

from core.plugin.loader import PluginLoader
from core.plugin.registry import PluginRegistry
from core.plugin.stub import StubPlugin


def test_plugin_loader_load_and_unload() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    plugin = StubPlugin()

    plugin_id = loader.load_from_instance(plugin)
    assert plugin_id == StubPlugin.plugin_id()
    assert registry.exists(plugin_id)

    loader.unload(plugin_id)
    assert not registry.exists(plugin_id)
