"""Helpers for publishing events and linking trace entries."""

from __future__ import annotations

from core.domain.models import TraceEntry, TraceStep
from core.events.interfaces import IEventBus
from core.events.models import DomainEvent
from core.metrics.context import get_correlation_id


def publish_event(event_bus: IEventBus | None, event: DomainEvent) -> DomainEvent:
    """Publish an event when a bus is configured."""
    if event_bus is not None:
        event_bus.publish(event)
    return event


def trace_for_event(
    event: DomainEvent,
    *,
    step: TraceStep,
    source: str,
    message: str,
    timestamp: str | None = None,
) -> TraceEntry:
    """Create a trace entry linked to a published domain event."""
    return TraceEntry(
        step=step,
        source=source,
        timestamp=timestamp or event.occurred_at,
        message=message,
        event_id=event.event_id,
        event_type=event.event_type,
        correlation_id=get_correlation_id(),
    )
