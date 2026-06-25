"""Capability catalog for RunAnalysis pre-validation."""

from __future__ import annotations

from core.application.result import Failure, Result
from core.common.error_codes import ErrorCode


class CapabilityCatalog:
    """Resolves capability availability from plugins and engine support policy."""

    def __init__(
        self,
        plugin_manager: object,
        engine_supported_capabilities: frozenset[str] | None = None,
    ) -> None:
        self._plugin_manager = plugin_manager
        self._engine_supported_capabilities = engine_supported_capabilities

    def validate(self, capability: str) -> Failure | None:
        """Return a failure when the capability cannot be executed."""
        plugins = self._plugins_with_capability(capability)
        if not plugins:
            return Result.fail(
                code=ErrorCode.CAPABILITY_NOT_FOUND,
                message=f"Capability not found: {capability}",
            )

        enabled_plugins = [
            plugin for plugin in plugins if plugin.metadata().enabled
        ]
        if not enabled_plugins:
            return Result.fail(
                code=ErrorCode.CAPABILITY_DISABLED,
                message=f"Capability is disabled: {capability}",
            )

        if (
            self._engine_supported_capabilities is not None
            and capability not in self._engine_supported_capabilities
        ):
            return Result.fail(
                code=ErrorCode.CAPABILITY_NOT_SUPPORTED,
                message=f"Engine does not support capability: {capability}",
            )

        return None

    def _plugins_with_capability(self, capability: str) -> list[object]:
        plugins: list[object] = []
        for plugin in self._plugin_manager.registry.list():
            metadata = plugin.metadata()
            if capability in metadata.capabilities:
                plugins.append(plugin)
        return plugins
