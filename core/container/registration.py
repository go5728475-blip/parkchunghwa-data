"""Service registration metadata."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ServiceLifetime(StrEnum):
    """Supported dependency lifetimes."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceRegistration:
    """Describes how a service is created and cached."""

    key: str
    lifetime: ServiceLifetime
    factory: Callable[[], Any] | None = None
    instance: Any | None = None

    def __post_init__(self) -> None:
        if self.instance is None and self.factory is None:
            msg = f"Service registration '{self.key}' requires a factory or instance."
            raise ValueError(msg)
