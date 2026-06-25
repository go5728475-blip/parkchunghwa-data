"""Tests for snapshot-aware replay."""

from __future__ import annotations

from core.events.event_types import AnalysisCompleted, AnalysisStarted, WorkflowStarted
from core.events.replay import ReplayEngine
from core.events.snapshot.in_memory_store import InMemorySnapshotStore
from core.events.snapshot.policy import SnapshotPolicy
from core.events.snapshot.models import Snapshot


def test_replay_from_snapshot_skips_prior_events() -> None:
    events = (
        WorkflowStarted(aggregate_id="wf-1", occurred_at="2026-01-01T00:00:00+00:00"),
        AnalysisStarted(aggregate_id="wf-1", occurred_at="2026-01-01T00:00:01+00:00"),
        AnalysisCompleted(aggregate_id="wf-1", occurred_at="2026-01-01T00:00:02+00:00"),
    )
    snapshot = Snapshot(
        aggregate_id="wf-1",
        aggregate_type="workflow",
        aggregate_version=2,
        state={"event_count": 2},
    )
    result = ReplayEngine().replay_from_snapshot(snapshot, events[2:])

    assert result.snapshot_applied is True
    assert result.replay_start_position == 2
    assert result.total_events == 1
    assert result.trace[0].event_type == "Snapshot"
    assert result.trace[1].event_type == "AnalysisCompleted"


def test_replay_for_aggregate_without_snapshot_uses_full_replay() -> None:
    events = (
        AnalysisStarted(aggregate_id="session-1"),
        AnalysisCompleted(aggregate_id="session-1"),
    )
    result = ReplayEngine(InMemorySnapshotStore()).replay_for_aggregate(
        "session-1",
        events,
    )

    assert result.snapshot_applied is False
    assert result.total_events == 2
    assert result.trace[0].event_type == "AnalysisStarted"


def test_replay_for_aggregate_with_snapshot_replays_tail_only() -> None:
    store = InMemorySnapshotStore()
    events = tuple(
        AnalysisStarted(
            aggregate_id="session-1",
            occurred_at=f"2026-01-01T00:00:0{index}+00:00",
        )
        for index in range(3)
    ) + (
        AnalysisCompleted(
            aggregate_id="session-1",
            occurred_at="2026-01-01T00:00:03+00:00",
        ),
    )
    snapshot = SnapshotPolicy(every_n_events=3).create_snapshot("session-1", events[:3])
    store.save(snapshot)

    result = ReplayEngine(store).replay_for_aggregate("session-1", events)

    assert result.snapshot_applied is True
    assert result.total_events == 1
    assert result.trace[-1].event_type == "AnalysisCompleted"
