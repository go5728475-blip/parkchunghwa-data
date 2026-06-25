"""Dependency injection container implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.container.errors import CircularDependencyError, ContainerError
from core.container.interfaces import IContainer
from core.container.registration import ServiceLifetime, ServiceRegistration


class Container(IContainer):
    """DI container with singleton and transient lifetimes."""

    def __init__(self) -> None:
        self._registrations: dict[str, ServiceRegistration] = {}
        self._singleton_cache: dict[str, Any] = {}
        self._overrides: dict[str, Any] = {}
        self._resolving: list[str] = []

    def register(
        self,
        key: str,
        factory: Callable[[], Any],
        *,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> None:
        if lifetime is ServiceLifetime.SCOPED:
            msg = "Scoped lifetime is reserved and not implemented."
            raise ContainerError(msg)
        self._registrations[key] = ServiceRegistration(
            key=key,
            lifetime=lifetime,
            factory=factory,
        )
        self._singleton_cache.pop(key, None)
        self._overrides.pop(key, None)

    def register_singleton(self, key: str, instance: Any) -> None:
        self._registrations[key] = ServiceRegistration(
            key=key,
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance,
        )
        self._singleton_cache[key] = instance
        self._overrides.pop(key, None)

    def register_factory(self, key: str, factory: Callable[[], Any]) -> None:
        """Register a lazy singleton factory resolved on first access."""
        self.register(key, factory, lifetime=ServiceLifetime.SINGLETON)

    def override(self, key: str, instance: Any) -> None:
        """Override a resolved dependency (typically for tests)."""
        self._overrides[key] = instance

    def resolve(self, key: str) -> Any:
        if key in self._overrides:
            return self._overrides[key]

        if key in self._resolving:
            chain = tuple(self._resolving + [key])
            raise CircularDependencyError(chain)

        registration = self._registrations.get(key)
        if registration is None:
            msg = f"Dependency not registered: {key}"
            raise ContainerError(msg)

        if registration.instance is not None:
            return registration.instance

        if registration.lifetime is ServiceLifetime.SINGLETON:
            if key in self._singleton_cache:
                return self._singleton_cache[key]
            if registration.factory is None:
                msg = f"Dependency not registered: {key}"
                raise ContainerError(msg)
            self._resolving.append(key)
            try:
                instance = registration.factory()
            finally:
                self._resolving.pop()
            self._singleton_cache[key] = instance
            return instance

        if registration.factory is None:
            msg = f"Dependency not registered: {key}"
            raise ContainerError(msg)

        self._resolving.append(key)
        try:
            return registration.factory()
        finally:
            self._resolving.pop()

    def exists(self, key: str) -> bool:
        return key in self._registrations or key in self._overrides

    def remove(self, key: str) -> None:
        self._registrations.pop(key, None)
        self._singleton_cache.pop(key, None)
        self._overrides.pop(key, None)

    def clear(self) -> None:
        self._registrations.clear()
        self._singleton_cache.clear()
        self._overrides.clear()
        self._resolving.clear()
