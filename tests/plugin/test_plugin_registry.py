"""Tests for plugin registry."""

from __future__ import annotations

import pytest

from core.plugin.errors import DuplicatePluginError, PluginNotFoundError
from core.plugin.registry import PluginRegistry
from core.plugin.stub import StubPlugin


def test_plugin_registry_register_get_list_unregister() -> None:
    registry = PluginRegistry()
    plugin = StubPlugin()

    registry.register(plugin)
    assert registry.exists(StubPlugin.plugin_id())
    assert registry.get(StubPlugin.plugin_id()) is plugin
    assert registry.list() == [plugin]
    assert registry.list_enabled() == [plugin]

    registry.unregister(StubPlugin.plugin_id())
    assert not registry.exists(StubPlugin.plugin_id())


def test_plugin_registry_duplicate_register_fails() -> None:
    registry = PluginRegistry()
    registry.register(StubPlugin())

    with pytest.raises(DuplicatePluginError):
        registry.register(StubPlugin())


def test_plugin_registry_list_enabled_excludes_disabled() -> None:
    registry = PluginRegistry()
    registry.register(StubPlugin(enabled=False))

    assert registry.list()
    assert registry.list_enabled() == []
