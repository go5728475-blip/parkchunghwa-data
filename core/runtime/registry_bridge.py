"""Runtime registry bridge for certified and runtime plugin state."""

from __future__ import annotations

from dataclasses import dataclass

from core.certification.models import DecisionStatus
from core.plugins.plugin_registry import CertificationPluginRegistry


@dataclass(frozen=True, kw_only=True)
class PluginStatus:
    """Combined plugin certification status."""

    plugin_id: str
    runtime_status: str | None
    certified: bool
    warnings: tuple[str, ...] = ()
    registered: bool = False


class RuntimeRegistryBridge:
    """Unified view over runtime and certified plugin registries."""

    def __init__(
        self,
        runtime_registry: CertificationPluginRegistry,
        certified_registry: object | None = None,
    ) -> None:
        self._runtime_registry = runtime_registry
        self._certified_registry = certified_registry

    def get_runtime_plugins(self) -> tuple[str, ...]:
        return self._runtime_registry.list_runtime_plugins()

    def get_certified_plugins(self) -> tuple[str, ...]:
        if self._certified_registry is None:
            return ()
        records = self._certified_registry.list_all()
        return tuple(record.plugin_id for record in records if record.certified)

    def get_plugin_status(self, plugin_id: str) -> PluginStatus:
        decision = self._runtime_registry.get_decision(plugin_id)
        runtime_status = decision.status.value if decision is not None else None
        certified = self.is_certified(plugin_id)
        warnings = self._runtime_registry.get_warnings(plugin_id)
        registered = self._runtime_registry.is_registered(plugin_id)
        return PluginStatus(
            plugin_id=plugin_id,
            runtime_status=runtime_status,
            certified=certified,
            warnings=warnings,
            registered=registered,
        )

    def is_certified(self, plugin_id: str) -> bool:
        if self._certified_registry is not None:
            return self._certified_registry.is_certified(plugin_id)
        decision = self._runtime_registry.get_decision(plugin_id)
        if decision is None:
            return False
        return decision.status is not DecisionStatus.FAIL

    def certification_summary(self) -> dict[str, object]:
        runtime_plugins = self.get_runtime_plugins()
        certified_plugins = self.get_certified_plugins()
        warning_plugins = tuple(
            plugin_id
            for plugin_id in runtime_plugins
            if self._runtime_registry.get_decision(plugin_id) is not None
            and self._runtime_registry.get_decision(plugin_id).status is DecisionStatus.WARN  # type: ignore[union-attr]
        )
        blocked_plugins = tuple(
            plugin_id
            for plugin_id in runtime_plugins
            if self._runtime_registry.get_decision(plugin_id) is not None
            and self._runtime_registry.get_decision(plugin_id).status is DecisionStatus.FAIL  # type: ignore[union-attr]
        )
        return {
            "runtime_plugins": runtime_plugins,
            "certified_plugins": certified_plugins,
            "warning_plugins": warning_plugins,
            "blocked_plugins": blocked_plugins,
            "audit_count": len(self._runtime_registry.get_audit_history()),
        }
