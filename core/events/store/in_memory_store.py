"""In-memory event store for published domain events."""

from __future__ import annotations

from core.events.models import DomainEvent
from core.events.store.interfaces import EventNotFoundError, IEventStore


class InMemoryEventStore(IEventStore):
    """Append-only in-memory store preserving publication order."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []
        self._index: dict[str, DomainEvent] = {}

    def append(self, event: DomainEvent) -> None:
        self._events.append(event)
        self._index[event.event_id] = event

    def append_many(self, events: tuple[DomainEvent, ...] | list[DomainEvent]) -> None:
        for event in events:
            self.append(event)

    def get(self, event_id: str) -> DomainEvent:
        event = self._index.get(event_id)
        if event is None:
            msg = f"Event not found: {event_id}"
            raise EventNotFoundError(msg)
        return event

    def list(self) -> tuple[DomainEvent, ...]:
        return tuple(self._events)

    def list_by_aggregate(self, aggregate_id: str) -> tuple[DomainEvent, ...]:
        return tuple(event for event in self._events if event.aggregate_id == aggregate_id)

    def clear(self) -> None:
        self._events.clear()
        self._index.clear()
