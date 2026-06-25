"""Capability-specific analysis stub plugins."""

from __future__ import annotations

from typing import Any

from core.domain.ids import PluginId
from core.domain.models import AnalysisSection
from core.domain.xai import build_plugin_analysis_section
from core.plugin.metadata import PluginMetadata


class _AnalysisStubPluginBase:
    """Shared placeholder implementation for analysis stub plugins."""

    def __init__(
        self,
        *,
        plugin_id: str,
        name: str,
        capability: str,
        placeholder: str,
        description: str,
        enabled: bool = True,
    ) -> None:
        self._plugin_id = PluginId(value=plugin_id)
        self._name = name
        self._capability = capability
        self._placeholder = placeholder
        self._description = description
        self._enabled = enabled
        self._initialized = False

    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id=self._plugin_id,
            name=self._name,
            version="0.1.0",
            description=self._description,
            capabilities=(self._capability,),
            dependencies=(),
            enabled=self._enabled,
        )

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def health_check(self) -> bool:
        return self._initialized or not self._enabled

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "result": self._placeholder,
            "capability": self._capability,
            "plugin_id": str(self._plugin_id),
            "input": input_data,
        }

    def create_analysis_section(self, input_data: dict[str, Any]) -> AnalysisSection:
        return build_plugin_analysis_section(
            capability=self._capability,
            title=self._name,
            content=self._placeholder,
            plugin_id=str(self._plugin_id),
        )

    @property
    def plugin_id(self) -> PluginId:
        return self._plugin_id


class MasterLockStubPlugin(_AnalysisStubPluginBase):
    """Placeholder plugin for MASTER LOCK analysis capability."""

    def __init__(self, enabled: bool = True) -> None:
        super().__init__(
            plugin_id="master_lock.stub",
            name="MASTER LOCK Stub Plugin",
            capability="master_lock.analysis",
            placeholder="master lock placeholder",
            description="Placeholder plugin for MASTER LOCK analysis routing.",
            enabled=enabled,
        )


class WealthStubPlugin(_AnalysisStubPluginBase):
    """Placeholder plugin for wealth analysis capability."""

    def __init__(self, enabled: bool = True) -> None:
        super().__init__(
            plugin_id="wealth.stub",
            name="Wealth Stub Plugin",
            capability="wealth.analysis",
            placeholder="wealth placeholder",
            description="Placeholder plugin for wealth analysis routing.",
            enabled=enabled,
        )


class CareerStubPlugin(_AnalysisStubPluginBase):
    """Placeholder plugin for career analysis capability."""

    def __init__(self, enabled: bool = True) -> None:
        super().__init__(
            plugin_id="career.stub",
            name="Career Stub Plugin",
            capability="career.analysis",
            placeholder="career placeholder",
            description="Placeholder plugin for career analysis routing.",
            enabled=enabled,
        )


class RelationshipStubPlugin(_AnalysisStubPluginBase):
    """Placeholder plugin for relationship analysis capability."""

    def __init__(self, enabled: bool = True) -> None:
        super().__init__(
            plugin_id="relationship.stub",
            name="Relationship Stub Plugin",
            capability="relationship.analysis",
            placeholder="relationship placeholder",
            description="Placeholder plugin for relationship analysis routing.",
            enabled=enabled,
        )
