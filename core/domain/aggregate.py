"""Aggregate root base class."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.domain.events import DomainEvent
from core.domain.ids import AggregateId


@dataclass
class AggregateRoot:
    """Base aggregate with domain event accumulation."""

    id: AggregateId
    _domain_events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    @property
    def domain_events(self) -> list[DomainEvent]:
        """Return a copy of pending domain events."""
        return list(self._domain_events)

    def record_event(self, event: DomainEvent) -> None:
        """Append a domain event to the pending outbox."""
        self._domain_events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Return pending events and clear the internal buffer."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def clear_events(self) -> None:
        """Clear pending domain events without returning them."""
        self._domain_events.clear()
