"""Tests for SQLite persistence serialization."""

from __future__ import annotations

from core.events.event_types import ProviderCalled, WorkflowStarted
from core.events.persistence.serialization import (
    event_to_record,
    record_to_event,
    record_to_snapshot,
    snapshot_to_record,
)
from core.events.snapshot.models import Snapshot


def test_event_serialization_round_trip() -> None:
    event = ProviderCalled(
        aggregate_id="openai.stub",
        payload={"provider_id": "openai.stub", "capability": "wealth.analysis"},
    )
    record = event_to_record(event)
    restored = record_to_event(
        (
            None,
            record["event_id"],
            record["event_type"],
            record["aggregate_id"],
            record["occurred_at"],
            record["payload_json"],
        ),
    )

    assert restored == event
    assert restored.event_type == "ProviderCalled"


def test_snapshot_serialization_round_trip() -> None:
    snapshot = Snapshot(
        aggregate_id="wf-1",
        aggregate_type="workflow",
        aggregate_version=3,
        state={"event_count": 3, "last_event_type": "WorkflowStarted"},
    )
    record = snapshot_to_record(snapshot)
    restored = record_to_snapshot(
        (
            None,
            record["snapshot_id"],
            record["aggregate_id"],
            record["aggregate_type"],
            record["aggregate_version"],
            record["created_at"],
            record["state_json"],
        ),
    )

    assert restored == snapshot


def test_unknown_event_type_deserializes_as_domain_event() -> None:
    record = event_to_record(
        WorkflowStarted(aggregate_id="wf-1", event_type="CustomEvent"),
    )
    record = {
        **record,
        "event_type": "CustomEvent",
    }
    restored = record_to_event(
        (
            None,
            record["event_id"],
            record["event_type"],
            record["aggregate_id"],
            record["occurred_at"],
            record["payload_json"],
        ),
    )

    assert restored.event_type == "CustomEvent"
    assert restored.aggregate_id == "wf-1"
