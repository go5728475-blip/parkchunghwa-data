"""Tests for in-memory event publisher."""

from __future__ import annotations

from core.domain.events import AnalysisSessionCreated, ReportCreated
from core.infrastructure.memory_event_publisher import InMemoryEventPublisher


def test_event_publisher_subscribe_and_publish() -> None:
    publisher = InMemoryEventPublisher()
    received: list[str] = []

    publisher.subscribe(
        "AnalysisSessionCreated",
        lambda event: received.append(event.aggregate_id),
    )
    event = AnalysisSessionCreated(aggregate_id="agg-1")
    publisher.publish(event)

    assert received == ["agg-1"]
    assert publisher.published_events == [event]


def test_event_publisher_wildcard_handler() -> None:
    publisher = InMemoryEventPublisher()
    wildcard_received: list[str] = []
    typed_received: list[str] = []

    publisher.subscribe("*", lambda event: wildcard_received.append(event.event_type))
    publisher.subscribe(
        "ReportCreated",
        lambda event: typed_received.append(event.aggregate_id),
    )

    session_event = AnalysisSessionCreated(aggregate_id="agg-1")
    report_event = ReportCreated(aggregate_id="agg-2")
    publisher.publish_many([session_event, report_event])

    assert wildcard_received == ["AnalysisSessionCreated", "ReportCreated"]
    assert typed_received == ["agg-2"]
    assert len(publisher.handler_calls) == 3


def test_event_publisher_does_not_call_unmatched_handlers() -> None:
    publisher = InMemoryEventPublisher()
    received: list[str] = []

    publisher.subscribe("ReportCreated", lambda event: received.append(event.aggregate_id))
    publisher.publish(AnalysisSessionCreated(aggregate_id="agg-1"))

    assert received == []
