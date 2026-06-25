"""Default certified plugin registry provider."""

from __future__ import annotations

from core.plugins.registry.certified import CertifiedPluginRegistry
from core.plugins.registry.factory import create_json_certified_plugin_registry
from core.plugins.registry.paths import (
    ensure_default_registry_directory,
    ensure_default_registry_file,
)

_default_registry: CertifiedPluginRegistry | None = None


def get_default_registry() -> CertifiedPluginRegistry:
    """Return the process-wide default certified plugin registry."""
    global _default_registry
    if _default_registry is None:
        ensure_default_registry_directory()
        registry_path = ensure_default_registry_file()
        _default_registry = create_json_certified_plugin_registry(registry_path)
    return _default_registry


def reset_default_registry() -> None:
    """Reset the cached default registry instance."""
    global _default_registry
    _default_registry = None


def set_default_registry_instance(registry: CertifiedPluginRegistry) -> None:
    """Set the cached default registry instance."""
    global _default_registry
    _default_registry = registry
