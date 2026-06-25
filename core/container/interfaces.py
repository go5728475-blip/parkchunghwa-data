"""Dependency injection container interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from core.container.registration import ServiceLifetime


class IContainer(ABC):
    """Port for dependency registration and resolution."""

    @abstractmethod
    def register(
        self,
        key: str,
        factory: Callable[[], Any],
        *,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> None:
        """Register a factory-backed service."""

    @abstractmethod
    def register_singleton(self, key: str, instance: Any) -> None:
        """Register a pre-built singleton instance."""

    @abstractmethod
    def resolve(self, key: str) -> Any:
        """Resolve a dependency by key."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return whether a dependency key is registered."""

    @abstractmethod
    def remove(self, key: str) -> None:
        """Remove a dependency registration."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all dependency registrations."""
