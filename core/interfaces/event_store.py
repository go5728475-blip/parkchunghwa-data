"""Event store interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from core.interfaces.event import IEvent


class IEventStore(ABC):
    """Persistence port for append-only event streams."""

    @abstractmethod
    async def append(self, aggregate_id: str, events: Sequence[IEvent]) -> None:
        """Append events to the stream of a single aggregate."""

    @abstractmethod
    async def load(self, aggregate_id: str) -> Sequence[IEvent]:
        """Load all events for the given aggregate."""
