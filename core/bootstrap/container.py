"""Backward-compatible re-exports for bootstrap container."""

from core.container.container import Container
from core.container.errors import ContainerError

__all__ = ["Container", "ContainerError"]
