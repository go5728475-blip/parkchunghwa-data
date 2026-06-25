"""Module loader manager."""

from __future__ import annotations

from core.container.interfaces import IContainer
from core.modules.interfaces import IModule
from core.modules.loader.errors import ModuleLoaderError
from core.modules.loader.interfaces import IModuleLoader
from core.modules.registry import ModuleRegistry


class LoaderManagerError(Exception):
    """Raised when loader manager operations fail."""


class LoaderManager:
    """Coordinates module loaders and registry integration."""

    def __init__(
        self,
        registry: ModuleRegistry,
        container: IContainer,
    ) -> None:
        self._registry = registry
        self._container = container
        self._loaders: list[IModuleLoader] = []
        self._module_loaders: dict[str, IModuleLoader] = {}
        self._paths: dict[str, str] = {}

    def register_loader(self, loader: IModuleLoader) -> None:
        self._loaders.append(loader)

    def resolve_loader(self, path: str) -> IModuleLoader:
        for loader in self._loaders:
            if loader.supports(path):
                return loader
        msg = f"No loader supports path: {path}"
        raise LoaderManagerError(msg)

    def load(self, path: str) -> str:
        loader = self.resolve_loader(path)
        module = loader.load(path)
        name = module.name()
        if self._registry.exists(name):
            loader.unload(name)
            msg = f"Module already registered: {name}"
            raise LoaderManagerError(msg)

        self._registry.register(module)
        module.register(self._container)
        self._registry.boot_module(name, self._container)
        self._module_loaders[name] = loader
        self._paths[name] = path
        return name

    def unload(self, module_name: str) -> None:
        if not self._registry.exists(module_name):
            msg = f"Module not registered: {module_name}"
            raise LoaderManagerError(msg)

        loader = self._module_loaders.get(module_name)
        if loader is not None:
            if self._registry.is_booted(module_name):
                self._registry.shutdown_module(module_name, self._container)
            loader.unload(module_name)
            self._module_loaders.pop(module_name, None)
            self._paths.pop(module_name, None)
        elif self._registry.is_booted(module_name):
            self._registry.shutdown_module(module_name, self._container)

        self._registry.unregister(module_name)

    def reload(self, module_name: str) -> str:
        path = self._paths.get(module_name)
        if path is None:
            msg = f"Dynamic module path not tracked: {module_name}"
            raise LoaderManagerError(msg)
        self.unload(module_name)
        return self.load(path)

    def list_loaded(self) -> tuple[str, ...]:
        loaded: list[str] = []
        for loader in self._loaders:
            loaded.extend(loader.list_loaded())
        return tuple(sorted(set(loaded)))

    def is_dynamic(self, module_name: str) -> bool:
        return module_name in self._paths
