"""Tests for plugin bootstrap wiring."""

from __future__ import annotations

from core.bootstrap.bootstrap import Bootstrap, CONTAINER_KEY_PLUGIN_MANAGER
from core.plugin.manager import PluginManager
from core.plugin.stub import StubPlugin


def test_bootstrap_resolves_plugin_manager() -> None:
    bootstrap = Bootstrap().build()
    manager = bootstrap.container().resolve(CONTAINER_KEY_PLUGIN_MANAGER)

    assert isinstance(manager, PluginManager)
    assert bootstrap.plugin_manager() is manager
    assert bootstrap.registry().has_service("plugin_manager")
    assert manager.registry.exists(StubPlugin.plugin_id())
    assert len(manager.registry.list()) == 5

    result = manager.execute(StubPlugin.plugin_id(), {"from": "bootstrap"})
    assert result["result"] == "stub placeholder"
