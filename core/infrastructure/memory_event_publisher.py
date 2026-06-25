"""In-memory event publisher implementation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from core.domain.events import DomainEvent

EventHandler = Callable[[DomainEvent], None]


class InMemoryEventPublisher:
    """In-memory publisher with per-type and wildcard subscriptions."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self.published_events: list[DomainEvent] = []
        self.handler_calls: list[tuple[str, DomainEvent]] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for a specific event type or '*' for all events."""
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publish a single event to matching handlers."""
        self.published_events.append(event)
        for handler in self._handlers.get(event.event_type, []):
            handler(event)
            self.handler_calls.append((event.event_type, event))
        for handler in self._handlers.get("*", []):
            handler(event)
            self.handler_calls.append(("*", event))

    def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple events in order."""
        for event in events:
            self.publish(event)
