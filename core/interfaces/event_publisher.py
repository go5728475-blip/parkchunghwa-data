"""Event publisher interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from core.interfaces.event import IEvent


class IEventPublisher(ABC):
    """Port for publishing domain events to external subscribers."""

    @abstractmethod
    async def publish(self, events: Sequence[IEvent]) -> None:
        """Publish one or more domain events."""
