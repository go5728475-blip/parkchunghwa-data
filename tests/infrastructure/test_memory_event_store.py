"""Tests for in-memory event store."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.domain.events import AnalysisSessionCreated, ReportCreated
from core.infrastructure.memory_event_store import InMemoryEventStore


def test_event_store_append_and_load_all() -> None:
    store = InMemoryEventStore()
    first = AnalysisSessionCreated(aggregate_id="agg-1")
    second = ReportCreated(aggregate_id="agg-2")

    store.append(first)
    store.append(second)

    assert store.load_all() == [first, second]


def test_event_store_append_many_preserves_occurred_at_order() -> None:
    store = InMemoryEventStore()
    earlier = AnalysisSessionCreated(
        aggregate_id="agg-1",
        occurred_at=datetime.now(UTC) - timedelta(hours=1),
    )
    later = ReportCreated(
        aggregate_id="agg-2",
        occurred_at=datetime.now(UTC),
    )

    store.append_many([later, earlier])

    assert store.load_all() == [earlier, later]


def test_event_store_load_by_aggregate_id() -> None:
    store = InMemoryEventStore()
    first = AnalysisSessionCreated(aggregate_id="agg-1")
    second = ReportCreated(aggregate_id="agg-2")
    third = AnalysisSessionCreated(aggregate_id="agg-1")

    store.append_many([first, second, third])

    assert store.load_by_aggregate_id("agg-1") == [first, third]


def test_event_store_load_by_event_type() -> None:
    store = InMemoryEventStore()
    session_event = AnalysisSessionCreated(aggregate_id="agg-1")
    report_event = ReportCreated(aggregate_id="agg-2")

    store.append_many([session_event, report_event])

    loaded = store.load_by_event_type("AnalysisSessionCreated")
    assert loaded == [session_event]


def test_event_store_clear() -> None:
    store = InMemoryEventStore()
    store.append(AnalysisSessionCreated(aggregate_id="agg-1"))
    store.clear()
    assert store.load_all() == []
