"""Tests for SDK base classes."""

from __future__ import annotations

from typing import Any

from sdk import BaseCapabilityPlugin, BaseModule, BasePlugin, PLUGIN_SDK_VERSION
from sdk.module import IModule
from sdk.plugin import IPlugin, PluginMetadata


class _ExampleModule(BaseModule):
    def __init__(self) -> None:
        super().__init__(
            name="health",
            version="1.0.0",
            author="Developer",
            description="Health module",
            capabilities=("health.analysis",),
        )


class _ExamplePlugin(BasePlugin):
    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return {"result": "ok", "input": input_data}


class _WealthCapabilityPlugin(BaseCapabilityPlugin):
    def __init__(self) -> None:
        super().__init__(
            plugin_id="wealth.stub",
            name="Wealth Plugin",
            capability="wealth.analysis",
        )


def test_base_module_implements_imodule_contract() -> None:
    module = _ExampleModule()

    assert isinstance(module, IModule)
    assert module.name() == "health"
    assert module.capabilities() == ("health.analysis",)


def test_base_module_lifecycle_flags() -> None:
    module = _ExampleModule()

    module.boot(object())
    assert module.loaded is True
    module.shutdown(object())
    assert module.loaded is False


def test_base_plugin_metadata_and_execution() -> None:
    plugin = _ExamplePlugin(
        plugin_id="generic.stub",
        name="Generic Plugin",
        version="0.1.0",
        description="Generic plugin",
        capabilities=("generic.analysis",),
    )

    assert isinstance(plugin, IPlugin)
    metadata = plugin.metadata()
    assert isinstance(metadata, PluginMetadata)
    assert plugin.execute({"value": 1})["result"] == "ok"


def test_base_capability_plugin_executes_with_capability() -> None:
    plugin = _WealthCapabilityPlugin()

    result = plugin.execute({"birth_year": 1990})

    assert result["capability"] == "wealth.analysis"
    assert result["plugin_id"] == "wealth.stub"


def test_plugin_sdk_version_is_defined() -> None:
    assert PLUGIN_SDK_VERSION == "1.0.0"
