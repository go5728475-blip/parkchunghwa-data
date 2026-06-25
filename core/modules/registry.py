"""Module registry."""

from __future__ import annotations

from core.container.interfaces import IContainer
from core.modules.interfaces import IModule
from core.modules.models import ModuleDescriptor


class ModuleRegistryError(Exception):
    """Raised when module registry operations fail."""


class ModuleRegistry:
    """Tracks registered modules and boot lifecycle."""

    def __init__(self) -> None:
        self._modules: dict[str, IModule] = {}
        self._booted: set[str] = set()

    def register(self, module: IModule) -> None:
        name = module.name()
        if name in self._modules:
            msg = f"Module already registered: {name}"
            raise ModuleRegistryError(msg)
        self._modules[name] = module

    def unregister(self, name: str) -> None:
        if name not in self._modules:
            msg = f"Module not registered: {name}"
            raise ModuleRegistryError(msg)
        self._modules.pop(name)
        self._booted.discard(name)

    def list(self) -> tuple[str, ...]:
        return tuple(sorted(self._modules))

    def exists(self, name: str) -> bool:
        return name in self._modules

    def resolve(self, name: str) -> IModule:
        module = self._modules.get(name)
        if module is None:
            msg = f"Module not registered: {name}"
            raise ModuleRegistryError(msg)
        return module

    def is_booted(self, name: str) -> bool:
        return name in self._booted

    def descriptor(self, name: str) -> ModuleDescriptor:
        module = self.resolve(name)
        return ModuleDescriptor(
            name=module.name(),
            version=module.version(),
            capabilities=module.capabilities(),
            loaded=self.is_booted(name),
        )

    def descriptors(self) -> tuple[ModuleDescriptor, ...]:
        return tuple(self.descriptor(name) for name in self.list())

    def register_all(self, container: IContainer) -> None:
        for name in self.list():
            self.resolve(name).register(container)

    def boot_all(self, container: IContainer) -> None:
        for name in self.list():
            if name in self._booted:
                continue
            self.resolve(name).boot(container)
            self._booted.add(name)

    def boot_module(self, name: str, container: IContainer) -> None:
        if name in self._booted:
            return
        self.resolve(name).boot(container)
        self._booted.add(name)

    def shutdown_module(self, name: str, container: IContainer) -> None:
        if name not in self._booted:
            return
        self.resolve(name).shutdown(container)
        self._booted.discard(name)

    def shutdown_all(self, container: IContainer) -> None:
        for name in reversed(self.list()):
            if name not in self._booted:
                continue
            self.resolve(name).shutdown(container)
            self._booted.discard(name)

    def clear(self) -> None:
        self._modules.clear()
        self._booted.clear()
