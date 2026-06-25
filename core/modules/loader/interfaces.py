"""Module loader interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.modules.interfaces import IModule


class IModuleLoader(ABC):
    """Port for loading external module packages."""

    @abstractmethod
    def load(self, path: str) -> IModule:
        """Load a module package from the given path."""

    @abstractmethod
    def unload(self, module_name: str) -> None:
        """Unload a previously loaded module."""

    @abstractmethod
    def reload(self, module_name: str) -> IModule:
        """Reload a previously loaded module."""

    @abstractmethod
    def list_loaded(self) -> tuple[str, ...]:
        """Return names of modules loaded by this loader."""

    @abstractmethod
    def supports(self, path: str) -> bool:
        """Return whether this loader can handle the given path."""
