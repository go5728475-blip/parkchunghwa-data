"""Tests for plugin manager."""

from __future__ import annotations

import pytest

from core.plugin.errors import PluginExecutionError, PluginNotFoundError
from core.plugin.loader import PluginLoader
from core.plugin.manager import PluginManager
from core.plugin.registry import PluginRegistry
from core.plugin.stub import StubPlugin


def test_plugin_manager_initialize_and_shutdown_all() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    manager = PluginManager(registry)
    plugin = StubPlugin()

    loader.load_from_instance(plugin)
    manager.initialize_all()
    assert plugin.health_check()

    manager.shutdown_all()
    assert not plugin._initialized  # noqa: SLF001


def test_plugin_manager_execute_success() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    manager = PluginManager(registry)
    loader.load_from_instance(StubPlugin())
    manager.initialize_all()

    result = manager.execute(StubPlugin.plugin_id(), {"sample": True})

    assert result["result"] == "stub placeholder"
    assert result["capability"] == "stub.analysis"


def test_plugin_manager_execute_disabled_plugin_fails() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    manager = PluginManager(registry)
    loader.load_from_instance(StubPlugin(enabled=False))

    with pytest.raises(PluginExecutionError, match="disabled"):
        manager.execute(StubPlugin.plugin_id(), {})


def test_plugin_manager_execute_missing_plugin_fails() -> None:
    manager = PluginManager(PluginRegistry())

    with pytest.raises(PluginNotFoundError):
        manager.execute(StubPlugin.plugin_id(), {})
