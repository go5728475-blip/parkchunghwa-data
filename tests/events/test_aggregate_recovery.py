"""Tests for aggregate recovery."""

from __future__ import annotations

from core.events.event_types import AnalysisCompleted, AnalysisStarted
from core.events.recovery import AggregateRecovery
from core.events.replay import ReplayEngine
from core.events.snapshot.in_memory_store import InMemorySnapshotStore
from core.events.snapshot.models import Snapshot
from core.events.snapshot.policy import SnapshotPolicy
from core.events.store.in_memory_store import InMemoryEventStore


def test_recover_without_snapshot_replays_all_events() -> None:
    event_store = InMemoryEventStore()
    events = (
        AnalysisStarted(aggregate_id="session-1"),
        AnalysisCompleted(aggregate_id="session-1"),
    )
    event_store.append_many(events)
    recovery = AggregateRecovery(
        event_store,
        InMemorySnapshotStore(),
        ReplayEngine(),
    )

    result = recovery.recover("session-1")

    assert result["snapshot_applied"] is False
    assert result["state"]["event_count"] == 2
    assert result["replay"].total_events == 2


def test_recover_with_snapshot_uses_generic_state() -> None:
    event_store = InMemoryEventStore()
    snapshot_store = InMemorySnapshotStore()
    events = (
        AnalysisStarted(aggregate_id="session-1"),
        AnalysisCompleted(aggregate_id="session-1"),
    )
    event_store.append_many(events)
    snapshot = SnapshotPolicy(every_n_events=1).create_snapshot("session-1", (events[0],))
    snapshot_store.save(snapshot)
    recovery = AggregateRecovery(
        event_store,
        snapshot_store,
        ReplayEngine(snapshot_store),
    )

    result = recovery.recover("session-1")

    assert result["snapshot_applied"] is True
    assert result["snapshot_version"] == 1
    assert result["state"]["event_count"] == 1
    assert result["state"]["replayed_event_count"] == 1
    assert result["replay"].trace[0].event_type == "Snapshot"


def test_factory_registers_aggregate_recovery() -> None:
    from core.bootstrap.factory import ApplicationFactory

    factory = ApplicationFactory()
    event_store = factory.create_event_store()
    snapshot_store = factory.create_snapshot_store()
    recovery = factory.create_aggregate_recovery(event_store, snapshot_store)

    assert isinstance(recovery, AggregateRecovery)
