"""SDK module interfaces and base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IModule(Protocol):
    """Public module contract for MASTER ENGINE plugins."""

    def name(self) -> str:
        """Return the unique module name."""

    def version(self) -> str:
        """Return the module version."""

    def capabilities(self) -> tuple[str, ...]:
        """Return capabilities provided by the module."""

    def register(self, container: Any) -> None:
        """Register module services in the engine container."""

    def boot(self, container: Any) -> None:
        """Boot the module after registration."""

    def shutdown(self, container: Any) -> None:
        """Shutdown the module during engine teardown."""


class BaseModule(IModule, ABC):
    """Base class for external MASTER ENGINE modules."""

    def __init__(
        self,
        *,
        name: str,
        version: str,
        capabilities: tuple[str, ...],
        author: str = "",
        description: str = "",
    ) -> None:
        if not name.strip():
            msg = "Module name cannot be empty."
            raise ValueError(msg)
        if not version.strip():
            msg = "Module version cannot be empty."
            raise ValueError(msg)
        if not capabilities:
            msg = "Module requires at least one capability."
            raise ValueError(msg)
        self._name = name.strip()
        self._version = version.strip()
        self._capabilities = tuple(capability.strip() for capability in capabilities)
        self._author = author.strip()
        self._description = description.strip()
        self._loaded = False

    def name(self) -> str:
        return self._name

    def version(self) -> str:
        return self._version

    def capabilities(self) -> tuple[str, ...]:
        return self._capabilities

    @property
    def author(self) -> str:
        return self._author

    @property
    def description(self) -> str:
        return self._description

    @property
    def loaded(self) -> bool:
        return self._loaded

    def register(self, container: Any) -> None:
        """Default no-op registration for SDK-only development."""

    def boot(self, container: Any) -> None:
        self._loaded = True

    def shutdown(self, container: Any) -> None:
        self._loaded = False
