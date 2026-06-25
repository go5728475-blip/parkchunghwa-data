"""Module system interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.container.interfaces import IContainer


class IModule(ABC):
    """Port for feature modules registered at application startup."""

    @abstractmethod
    def name(self) -> str:
        """Return the unique module name."""

    @abstractmethod
    def version(self) -> str:
        """Return the module version."""

    @abstractmethod
    def capabilities(self) -> tuple[str, ...]:
        """Return capabilities provided by the module."""

    @abstractmethod
    def register(self, container: IContainer) -> None:
        """Register module services in the container."""

    @abstractmethod
    def boot(self, container: IContainer) -> None:
        """Boot the module after registration."""

    @abstractmethod
    def shutdown(self, container: IContainer) -> None:
        """Shutdown the module during application teardown."""
