"""Tests for published domain event store."""

from __future__ import annotations

import pytest

from core.events.event_types import AnalysisCompleted, AnalysisStarted, WorkflowStarted
from core.events.store.in_memory_store import InMemoryEventStore
from core.events.store.interfaces import EventNotFoundError


def test_append_and_get() -> None:
    store = InMemoryEventStore()
    event = AnalysisStarted(aggregate_id="session-1")

    store.append(event)

    assert store.get(event.event_id) == event


def test_append_many_preserves_order() -> None:
    store = InMemoryEventStore()
    first = WorkflowStarted(aggregate_id="wf-1")
    second = AnalysisStarted(aggregate_id="session-1")
    third = AnalysisCompleted(aggregate_id="session-1")

    store.append_many((first, second, third))

    assert store.list() == (first, second, third)


def test_list_returns_all_events() -> None:
    store = InMemoryEventStore()
    events = [
        WorkflowStarted(aggregate_id="wf-1"),
        AnalysisStarted(aggregate_id="session-1"),
    ]
    store.append_many(events)

    assert store.list() == tuple(events)


def test_list_by_aggregate_filters_events() -> None:
    store = InMemoryEventStore()
    workflow_event = WorkflowStarted(aggregate_id="wf-1")
    analysis_event = AnalysisStarted(aggregate_id="session-1")
    store.append_many((workflow_event, analysis_event))

    assert store.list_by_aggregate("wf-1") == (workflow_event,)
    assert store.list_by_aggregate("session-1") == (analysis_event,)


def test_clear_removes_events() -> None:
    store = InMemoryEventStore()
    event = AnalysisStarted(aggregate_id="session-1")
    store.append(event)

    store.clear()

    assert store.list() == ()
    with pytest.raises(EventNotFoundError):
        store.get(event.event_id)


def test_get_missing_event_raises() -> None:
    store = InMemoryEventStore()

    with pytest.raises(EventNotFoundError):
        store.get("missing-event-id")
