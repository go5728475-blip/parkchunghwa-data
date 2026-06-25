"""Event replay engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from core.events.models import DomainEvent
from core.events.snapshot.interfaces import ISnapshotStore
from core.events.snapshot.models import Snapshot
from core.events.snapshot.replay_support import events_after_snapshot


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, kw_only=True)
class ReplayTraceEntry:
    """Single step in a replay trace."""

    order: int
    event_id: str
    event_type: str
    aggregate_id: str
    occurred_at: str
    message: str


@dataclass(frozen=True, kw_only=True)
class ReplayResult:
    """Output from replaying stored domain events."""

    replay_id: str
    total_events: int
    started_at: str
    finished_at: str
    trace: tuple[ReplayTraceEntry, ...] = field(default_factory=tuple)
    snapshot_applied: bool = False
    replay_start_position: int = 0

    def __post_init__(self) -> None:
        if self.trace is None:
            object.__setattr__(self, "trace", ())


class ReplayEngine:
    """Replays stored events with optional snapshot acceleration."""

    def __init__(self, snapshot_store: ISnapshotStore | None = None) -> None:
        self._snapshot_store = snapshot_store

    def replay(self, events: tuple[DomainEvent, ...] | list[DomainEvent]) -> ReplayResult:
        """Replay events and produce a trace without restoring domain state."""
        started_at = _utc_timestamp()
        ordered = sorted(events, key=lambda event: event.occurred_at)
        trace = self._build_event_trace(ordered, start_order=1)
        return ReplayResult(
            replay_id=str(uuid4()),
            total_events=len(ordered),
            started_at=started_at,
            finished_at=_utc_timestamp(),
            trace=trace,
            snapshot_applied=False,
            replay_start_position=0,
        )

    def replay_from_snapshot(
        self,
        snapshot: Snapshot,
        events: tuple[DomainEvent, ...] | list[DomainEvent],
    ) -> ReplayResult:
        """Replay only events recorded after a snapshot."""
        started_at = _utc_timestamp()
        ordered = sorted(events, key=lambda event: event.occurred_at)
        trace = (
            ReplayTraceEntry(
                order=1,
                event_id=snapshot.snapshot_id,
                event_type="Snapshot",
                aggregate_id=snapshot.aggregate_id,
                occurred_at=snapshot.created_at,
                message=(
                    f"Loaded snapshot version {snapshot.aggregate_version} "
                    f"for {snapshot.aggregate_type}"
                ),
            ),
            *self._build_event_trace(ordered, start_order=2),
        )
        return ReplayResult(
            replay_id=str(uuid4()),
            total_events=len(ordered),
            started_at=started_at,
            finished_at=_utc_timestamp(),
            trace=trace,
            snapshot_applied=True,
            replay_start_position=snapshot.aggregate_version,
        )

    def replay_for_aggregate(
        self,
        aggregate_id: str,
        events: tuple[DomainEvent, ...] | list[DomainEvent],
        snapshot_store: ISnapshotStore | None = None,
    ) -> ReplayResult:
        """Replay using the latest snapshot when available."""
        store = snapshot_store or self._snapshot_store
        if store is not None:
            snapshot = store.get_latest(aggregate_id)
            if snapshot is not None:
                remaining = events_after_snapshot(snapshot, events)
                return self.replay_from_snapshot(snapshot, remaining)
        return self.replay(events)

    @staticmethod
    def _build_event_trace(
        ordered_events: list[DomainEvent] | tuple[DomainEvent, ...],
        *,
        start_order: int,
    ) -> tuple[ReplayTraceEntry, ...]:
        return tuple(
            ReplayTraceEntry(
                order=index,
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                occurred_at=event.occurred_at,
                message=(
                    f"Replayed {event.event_type} "
                    f"for aggregate {event.aggregate_id}"
                ),
            )
            for index, event in enumerate(ordered_events, start=start_order)
        )
