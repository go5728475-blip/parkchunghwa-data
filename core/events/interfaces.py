"""Event bus interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from core.events.models import DomainEvent

EventHandler = Callable[[DomainEvent], None]


class IEventBus(ABC):
    """Port for synchronous in-process domain event publication."""

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to subscribers."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for an event type."""

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler for an event type."""

    @abstractmethod
    def subscribe_all(self, handler: EventHandler) -> None:
        """Register a handler invoked for every published event before typed handlers."""

    @abstractmethod
    def unsubscribe_all(self, handler: EventHandler) -> None:
        """Remove a global handler."""
