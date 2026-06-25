"""Module boot sequence helpers."""

from __future__ import annotations

from core.container.interfaces import IContainer
from core.modules.builtin import create_builtin_modules
from core.modules.registry import ModuleRegistry


def create_module_registry() -> ModuleRegistry:
    """Create a module registry with builtin modules registered."""
    registry = ModuleRegistry()
    for module in create_builtin_modules():
        registry.register(module)
    return registry


def boot_modules(container: IContainer, registry: ModuleRegistry) -> None:
    """Register and boot all modules in order."""
    registry.register_all(container)
    registry.boot_all(container)
    container.register_singleton("module_registry", registry)


def shutdown_modules(container: IContainer, registry: ModuleRegistry) -> None:
    """Shutdown all booted modules."""
    registry.shutdown_all(container)
