"""In-memory synchronous event bus."""

from __future__ import annotations

from collections import defaultdict

from core.events.interfaces import EventHandler, IEventBus
from core.events.models import DomainEvent


class InMemoryEventBus(IEventBus):
    """Synchronous event bus storing recent events for inspection."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._global_handlers: list[EventHandler] = []
        self._recent_events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self._recent_events.append(event)
        for handler in list(self._global_handlers):
            handler(event)
        for handler in list(self._handlers.get(event.event_type, [])):
            handler(event)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        if handler not in self._global_handlers:
            self._global_handlers.append(handler)

    def unsubscribe_all(self, handler: EventHandler) -> None:
        if handler in self._global_handlers:
            self._global_handlers.remove(handler)

    def recent_events(self) -> tuple[DomainEvent, ...]:
        """Return events published during this process lifetime."""
        return tuple(self._recent_events)

    def clear(self) -> None:
        """Remove handlers and stored events."""
        self._handlers.clear()
        self._global_handlers.clear()
        self._recent_events.clear()
