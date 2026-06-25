"""Tests for event replay engine."""

from __future__ import annotations

from core.events.event_types import (
    AnalysisCompleted,
    AnalysisStarted,
    CapabilityExecuted,
    WorkflowCompleted,
    WorkflowStarted,
)
from core.events.replay import ReplayEngine
from core.bootstrap.factory import ApplicationFactory


def test_replay_orders_events_chronologically() -> None:
    events = [
        AnalysisCompleted(
            aggregate_id="session-1",
            occurred_at="2026-01-03T10:00:02+00:00",
        ),
        AnalysisStarted(
            aggregate_id="session-1",
            occurred_at="2026-01-03T10:00:00+00:00",
        ),
        CapabilityExecuted(
            aggregate_id="wealth.analysis",
            occurred_at="2026-01-03T10:00:01+00:00",
        ),
    ]
    result = ReplayEngine().replay(events)

    assert result.total_events == 3
    assert [entry.event_type for entry in result.trace] == [
        "AnalysisStarted",
        "CapabilityExecuted",
        "AnalysisCompleted",
    ]


def test_replay_trace_contains_event_metadata() -> None:
    event = WorkflowStarted(aggregate_id="wf-1", payload={"name": "Test"})
    result = ReplayEngine().replay((event,))

    trace_entry = result.trace[0]
    assert trace_entry.event_id == event.event_id
    assert trace_entry.event_type == "WorkflowStarted"
    assert trace_entry.aggregate_id == "wf-1"
    assert trace_entry.order == 1
    assert "Replayed WorkflowStarted" in trace_entry.message


def test_replay_workflow_events() -> None:
    events = (
        WorkflowStarted(aggregate_id="wf-1"),
        WorkflowCompleted(aggregate_id="wf-1"),
    )
    result = ReplayEngine().replay(events)

    assert result.total_events == 2
    assert result.started_at
    assert result.finished_at
    assert result.replay_id


def test_factory_registers_replay_engine() -> None:
    engine = ApplicationFactory().create_replay_engine()
    assert isinstance(engine, ReplayEngine)
