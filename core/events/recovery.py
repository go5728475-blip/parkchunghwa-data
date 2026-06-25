"""Aggregate recovery from snapshots and events."""

from __future__ import annotations

from typing import Any

from core.events.replay import ReplayEngine, ReplayResult
from core.events.snapshot.interfaces import ISnapshotStore
from core.events.snapshot.policy import SnapshotPolicy
from core.events.snapshot.replay_support import events_after_snapshot
from core.events.store.interfaces import IEventStore


class AggregateRecovery:
    """Recover generic aggregate state using snapshots and replay."""

    def __init__(
        self,
        event_store: IEventStore,
        snapshot_store: ISnapshotStore,
        replay_engine: ReplayEngine,
        policy: SnapshotPolicy | None = None,
    ) -> None:
        self._event_store = event_store
        self._snapshot_store = snapshot_store
        self._replay_engine = replay_engine
        self._policy = policy or SnapshotPolicy()

    def recover(self, aggregate_id: str) -> dict[str, Any]:
        """Recover generic state without restoring domain aggregates."""
        events = self._event_store.list_by_aggregate(aggregate_id)
        snapshot = self._snapshot_store.get_latest(aggregate_id)

        if snapshot is None:
            replay_result = self._replay_engine.replay(events)
            return {
                "aggregate_id": aggregate_id,
                "snapshot_applied": False,
                "state": self._build_state_without_snapshot(aggregate_id, events, replay_result),
                "replay": replay_result,
            }

        remaining = events_after_snapshot(snapshot, events)
        replay_result = self._replay_engine.replay_from_snapshot(snapshot, remaining)
        state = dict(snapshot.state)
        state["replayed_event_count"] = replay_result.total_events
        state["replayed_event_types"] = [event.event_type for event in remaining]
        return {
            "aggregate_id": aggregate_id,
            "snapshot_applied": True,
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_version": snapshot.aggregate_version,
            "state": state,
            "replay": replay_result,
        }

    def _build_state_without_snapshot(
        self,
        aggregate_id: str,
        events: tuple[DomainEvent, ...],
        replay_result: ReplayResult,
    ) -> dict[str, Any]:
        if not events:
            return {
                "aggregate_id": aggregate_id,
                "event_count": 0,
                "replayed_event_count": replay_result.total_events,
            }
        return {
            **self._policy.build_state(aggregate_id, events),
            "replayed_event_count": replay_result.total_events,
        }
