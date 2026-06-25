"""Provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IProvider(ABC):
    """Provider-independent port for external capability adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Canonical provider identifier."""

    @abstractmethod
    async def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Invoke a provider-specific operation."""
