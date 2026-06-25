"""Helpers for snapshot-aware replay."""

from __future__ import annotations

from core.events.models import DomainEvent
from core.events.snapshot.models import Snapshot


def events_after_snapshot(
    snapshot: Snapshot,
    events: tuple[DomainEvent, ...] | list[DomainEvent],
) -> tuple[DomainEvent, ...]:
    """Return events recorded after a snapshot version."""
    ordered = tuple(sorted(events, key=lambda event: event.occurred_at))
    return ordered[snapshot.aggregate_version:]
