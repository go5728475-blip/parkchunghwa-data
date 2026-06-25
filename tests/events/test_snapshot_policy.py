"""Tests for snapshot policy."""

from __future__ import annotations

from core.events.event_types import AnalysisCompleted, AnalysisStarted
from core.events.snapshot.policy import SnapshotPolicy


def test_policy_triggers_every_n_events() -> None:
    policy = SnapshotPolicy(every_n_events=3)

    assert policy.should_snapshot(1) is False
    assert policy.should_snapshot(2) is False
    assert policy.should_snapshot(3) is True
    assert policy.should_snapshot(6) is True


def test_create_snapshot_builds_generic_state() -> None:
    policy = SnapshotPolicy(every_n_events=2)
    events = (
        AnalysisStarted(aggregate_id="session-1"),
        AnalysisCompleted(aggregate_id="session-1"),
    )
    snapshot = policy.create_snapshot("session-1", events)

    assert snapshot.aggregate_id == "session-1"
    assert snapshot.aggregate_type == "analysis"
    assert snapshot.aggregate_version == 2
    assert snapshot.state["event_count"] == 2
    assert snapshot.state["last_event_type"] == "AnalysisCompleted"
