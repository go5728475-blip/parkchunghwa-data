"""Certified plugin registry resolution helpers."""

from __future__ import annotations

from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.registry.provider import get_default_registry

CONTAINER_KEY_CERTIFIED_PLUGIN_REGISTRY = "certified_plugin_registry"


def resolve_certified_registry(container: object | None = None) -> object:
    """Resolve the certified plugin registry from DI or the default provider."""
    if container is not None and container.exists(CONTAINER_KEY_CERTIFIED_PLUGIN_REGISTRY):
        return container.resolve(CONTAINER_KEY_CERTIFIED_PLUGIN_REGISTRY)
    return get_default_registry()


def module_certification_display(
    certified_registry: object,
    module_name: str,
) -> tuple[str, str]:
    """Return certified status and compatibility level for a module."""
    record = certified_registry.get(module_name)
    if record is None:
        return "no", PluginCompatibilityLevel.UNKNOWN.value
    certified = "yes" if record.certified else "no"
    return certified, record.compatibility_level.value
