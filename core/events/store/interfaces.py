"""Event store interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.events.models import DomainEvent


class EventNotFoundError(Exception):
    """Raised when an event cannot be found in the store."""


class IEventStore(ABC):
    """Port for append-only domain event persistence."""

    @abstractmethod
    def append(self, event: DomainEvent) -> None:
        """Append a single domain event."""

    @abstractmethod
    def append_many(self, events: tuple[DomainEvent, ...] | list[DomainEvent]) -> None:
        """Append multiple domain events preserving order."""

    @abstractmethod
    def get(self, event_id: str) -> DomainEvent:
        """Return a stored event by identifier."""

    @abstractmethod
    def list(self) -> tuple[DomainEvent, ...]:
        """Return all stored events in append order."""

    @abstractmethod
    def list_by_aggregate(self, aggregate_id: str) -> tuple[DomainEvent, ...]:
        """Return events for an aggregate in append order."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored events."""
