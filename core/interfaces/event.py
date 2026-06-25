"""Domain event interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID


class IEvent(ABC):
    """Marker interface for domain events in event-sourced aggregates."""

    @property
    @abstractmethod
    def event_id(self) -> UUID:
        """Unique identifier of the event."""

    @property
    @abstractmethod
    def aggregate_id(self) -> str:
        """Identifier of the aggregate that produced the event."""

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Canonical event type name."""

    @property
    @abstractmethod
    def occurred_at(self) -> datetime:
        """Timestamp when the event occurred."""

    @property
    @abstractmethod
    def payload(self) -> dict[str, Any]:
        """Event payload as a serializable dictionary."""

    @property
    @abstractmethod
    def version(self) -> int:
        """Aggregate version after applying this event."""
