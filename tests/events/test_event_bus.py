"""Tests for in-memory event bus."""

from __future__ import annotations

from core.events.event_types import AnalysisStarted
from core.events.in_memory_bus import InMemoryEventBus
from core.events.models import DomainEvent


def test_publish_stores_event() -> None:
    bus = InMemoryEventBus()
    event = AnalysisStarted(aggregate_id="session-1", payload={"capability": "stub.analysis"})

    bus.publish(event)

    assert bus.recent_events() == (event,)


def test_subscribe_receives_published_event() -> None:
    bus = InMemoryEventBus()
    received: list[DomainEvent] = []
    bus.subscribe("AnalysisStarted", received.append)
    event = AnalysisStarted(aggregate_id="session-1")

    bus.publish(event)

    assert received == [event]


def test_unsubscribe_stops_delivery() -> None:
    bus = InMemoryEventBus()
    received: list[DomainEvent] = []

    def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("AnalysisStarted", handler)
    bus.unsubscribe("AnalysisStarted", handler)
    bus.publish(AnalysisStarted(aggregate_id="session-1"))

    assert received == []


def test_subscribe_all_runs_before_typed_handlers() -> None:
    bus = InMemoryEventBus()
    order: list[str] = []

    bus.subscribe_all(lambda _event: order.append("global"))
    bus.subscribe("AnalysisStarted", lambda _event: order.append("typed"))
    bus.publish(AnalysisStarted(aggregate_id="session-1"))

    assert order == ["global", "typed"]


def test_publish_persists_to_store_via_subscribe_all() -> None:
    from core.events.store.in_memory_store import InMemoryEventStore
    from core.events.wiring import wire_event_store

    bus = InMemoryEventBus()
    store = InMemoryEventStore()
    wire_event_store(bus, store)
    event = AnalysisStarted(aggregate_id="session-1")

    bus.publish(event)

    assert store.list() == (event,)
