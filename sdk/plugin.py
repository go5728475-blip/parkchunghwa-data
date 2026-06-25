"""SDK plugin interfaces and base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, kw_only=True)
class PluginMetadata:
    """Metadata exposed by a plugin implementation."""

    plugin_id: str
    name: str
    version: str
    description: str
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    enabled: bool = True


@runtime_checkable
class IPlugin(Protocol):
    """Public plugin contract for MASTER ENGINE capability plugins."""

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


class BasePlugin(IPlugin, ABC):
    """Base class for generic MASTER ENGINE plugins."""

    def __init__(
        self,
        *,
        plugin_id: str,
        name: str,
        version: str,
        description: str,
        capabilities: tuple[str, ...] = (),
        dependencies: tuple[str, ...] = (),
        enabled: bool = True,
    ) -> None:
        self._plugin_id = plugin_id.strip()
        self._name = name.strip()
        self._version = version.strip()
        self._description = description.strip()
        self._capabilities = tuple(item.strip() for item in capabilities)
        self._dependencies = tuple(item.strip() for item in dependencies)
        self._enabled = enabled
        self._initialized = False

    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id=self._plugin_id,
            name=self._name,
            version=self._version,
            description=self._description,
            capabilities=self._capabilities,
            dependencies=self._dependencies,
            enabled=self._enabled,
        )

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def health_check(self) -> bool:
        return self._initialized or not self._enabled

    @abstractmethod
    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute plugin logic."""


class BaseCapabilityPlugin(BasePlugin):
    """Base class for single-capability analysis plugins."""

    def __init__(
        self,
        *,
        plugin_id: str,
        name: str,
        capability: str,
        version: str = "0.1.0",
        description: str = "",
        placeholder: str = "analysis placeholder",
        enabled: bool = True,
    ) -> None:
        super().__init__(
            plugin_id=plugin_id,
            name=name,
            version=version,
            description=description or f"Capability plugin for {capability}.",
            capabilities=(capability,),
            enabled=enabled,
        )
        self._capability = capability.strip()
        self._placeholder = placeholder

    @property
    def capability(self) -> str:
        return self._capability

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "result": self._placeholder,
            "capability": self._capability,
            "plugin_id": self._plugin_id,
            "input": input_data,
        }
