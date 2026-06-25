"""Event bus and event store wiring."""

from __future__ import annotations

from core.events.interfaces import IEventBus
from core.events.models import DomainEvent
from core.events.snapshot.interfaces import ISnapshotStore
from core.events.snapshot.policy import SnapshotPolicy
from core.events.store.interfaces import IEventStore


def wire_event_store(event_bus: IEventBus, event_store: IEventStore) -> None:
    """Persist every published event before typed subscribers run."""
    event_bus.subscribe_all(event_store.append)


def wire_snapshot_policy(
    event_bus: IEventBus,
    event_store: IEventStore,
    snapshot_store: ISnapshotStore,
    policy: SnapshotPolicy,
) -> None:
    """Create snapshots after events are persisted when policy matches."""

    def maybe_snapshot(event: DomainEvent) -> None:
        aggregate_id = event.aggregate_id
        if not aggregate_id:
            return
        events = event_store.list_by_aggregate(aggregate_id)
        if policy.should_snapshot(len(events)):
            snapshot_store.save(policy.create_snapshot(aggregate_id, events))

    event_bus.subscribe_all(maybe_snapshot)
