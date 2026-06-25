"""Reserved loader interfaces for future package formats."""

from __future__ import annotations

from core.modules.interfaces import IModule
from core.modules.loader.errors import ModuleLoaderError
from core.modules.loader.interfaces import IModuleLoader


class ZipModuleLoader(IModuleLoader):
    """Reserved ZIP package loader (not implemented in this sprint)."""

    def load(self, path: str) -> IModule:
        msg = "ZIP module loader is not implemented."
        raise ModuleLoaderError(msg)

    def unload(self, module_name: str) -> None:
        return

    def reload(self, module_name: str) -> IModule:
        msg = "ZIP module loader is not implemented."
        raise ModuleLoaderError(msg)

    def list_loaded(self) -> tuple[str, ...]:
        return ()

    def supports(self, path: str) -> bool:
        return path.lower().endswith(".zip")


class WhlModuleLoader(IModuleLoader):
    """Reserved WHL package loader (not implemented in this sprint)."""

    def load(self, path: str) -> IModule:
        msg = "WHL module loader is not implemented."
        raise ModuleLoaderError(msg)

    def unload(self, module_name: str) -> None:
        return

    def reload(self, module_name: str) -> IModule:
        msg = "WHL module loader is not implemented."
        raise ModuleLoaderError(msg)

    def list_loaded(self) -> tuple[str, ...]:
        return ()

    def supports(self, path: str) -> bool:
        return path.lower().endswith(".whl")
