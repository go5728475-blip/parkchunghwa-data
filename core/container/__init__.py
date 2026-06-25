"""Dependency injection container."""

from core.container.container import Container
from core.container.errors import CircularDependencyError, ContainerError
from core.container.interfaces import IContainer
from core.container.registration import ServiceLifetime, ServiceRegistration

__all__ = [
    "CircularDependencyError",
    "Container",
    "ContainerError",
    "IContainer",
    "ServiceLifetime",
    "ServiceRegistration",
]
