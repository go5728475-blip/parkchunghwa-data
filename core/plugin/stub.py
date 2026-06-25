"""Stub plugin for development and testing."""

from __future__ import annotations

from typing import Any

from core.domain.ids import PluginId
from core.domain.models import AnalysisSection
from core.domain.xai import build_plugin_analysis_section
from core.plugin.metadata import PluginMetadata

_STUB_PLUGIN_ID = PluginId(value="stub.plugin")


class StubPlugin:
    """Placeholder plugin without interpretation logic."""

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._initialized = False

    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id=_STUB_PLUGIN_ID,
            name="Stub Plugin",
            version="0.1.0",
            description="Placeholder plugin for plugin foundation testing.",
            capabilities=("stub.analysis",),
            dependencies=(),
            enabled=self._enabled,
        )

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def health_check(self) -> bool:
        return self._initialized or not self.metadata().enabled

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "result": "stub placeholder",
            "capability": "stub.analysis",
            "input": input_data,
        }

    def create_analysis_section(self, input_data: dict[str, Any]) -> AnalysisSection:
        return build_plugin_analysis_section(
            capability="stub.analysis",
            title="Stub Plugin Result",
            content="stub placeholder",
            plugin_id=str(_STUB_PLUGIN_ID),
        )

    @classmethod
    def plugin_id(cls) -> PluginId:
        return _STUB_PLUGIN_ID
