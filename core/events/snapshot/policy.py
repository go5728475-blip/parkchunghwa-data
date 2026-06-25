"""Snapshot creation policy."""

from __future__ import annotations

from dataclasses import dataclass

from core.events.models import DomainEvent
from core.events.snapshot.models import Snapshot


def infer_aggregate_type(event_type: str) -> str:
    """Infer a generic aggregate type label from an event type."""
    if event_type.startswith("Workflow"):
        return "workflow"
    if event_type.startswith("Analysis") or event_type in {
        "CapabilityExecuted",
        "ProviderCalled",
        "ProviderCompleted",
    }:
        return "analysis"
    if event_type.startswith("Report"):
        return "report"
    return "generic"


@dataclass(frozen=True, kw_only=True)
class SnapshotPolicy:
    """Policy controlling when snapshots are created."""

    every_n_events: int = 50

    def __post_init__(self) -> None:
        if self.every_n_events < 1:
            msg = "every_n_events must be at least 1."
            raise ValueError(msg)

    def should_snapshot(self, aggregate_event_count: int) -> bool:
        """Return True when a snapshot should be created."""
        return aggregate_event_count > 0 and aggregate_event_count % self.every_n_events == 0

    def build_state(
        self,
        aggregate_id: str,
        events: tuple[DomainEvent, ...],
    ) -> dict[str, object]:
        """Build a generic snapshot state from aggregate events."""
        ordered = sorted(events, key=lambda event: event.occurred_at)
        last_event = ordered[-1]
        return {
            "aggregate_id": aggregate_id,
            "event_count": len(ordered),
            "last_event_id": last_event.event_id,
            "last_event_type": last_event.event_type,
            "last_occurred_at": last_event.occurred_at,
            "event_types": [event.event_type for event in ordered],
        }

    def create_snapshot(
        self,
        aggregate_id: str,
        events: tuple[DomainEvent, ...],
    ) -> Snapshot:
        """Create a snapshot for an aggregate at the current event count."""
        ordered = sorted(events, key=lambda event: event.occurred_at)
        last_event = ordered[-1]
        return Snapshot(
            aggregate_id=aggregate_id,
            aggregate_type=infer_aggregate_type(last_event.event_type),
            aggregate_version=len(ordered),
            state=self.build_state(aggregate_id, events),
        )
