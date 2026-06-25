"""In-memory event store implementation."""

from __future__ import annotations

from core.domain.events import DomainEvent


class InMemoryEventStore:
    """Append-only in-memory event store ordered by occurred_at."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        """Append a single domain event."""
        self._events.append(event)
        self._events.sort(key=lambda item: item.occurred_at)

    def append_many(self, events: list[DomainEvent]) -> None:
        """Append multiple domain events preserving occurred_at order."""
        self._events.extend(events)
        self._events.sort(key=lambda item: item.occurred_at)

    def load_all(self) -> list[DomainEvent]:
        """Return all stored events in occurred_at order."""
        return list(self._events)

    def load_by_aggregate_id(self, aggregate_id: str) -> list[DomainEvent]:
        """Return events for a single aggregate in occurred_at order."""
        return [
            event
            for event in self._events
            if event.aggregate_id == aggregate_id
        ]

    def load_by_event_type(self, event_type: str) -> list[DomainEvent]:
        """Return events matching the given event type in occurred_at order."""
        return [
            event
            for event in self._events
            if event.event_type == event_type
        ]

    def clear(self) -> None:
        """Remove all stored events."""
        self._events.clear()
