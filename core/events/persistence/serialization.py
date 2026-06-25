"""Serialization for persisted events and snapshots."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from core.events.event_types import (
    AnalysisCompleted,
    AnalysisStarted,
    CapabilityExecuted,
    ProviderCalled,
    ProviderCompleted,
    ReportBuilt,
    ReportExported,
    TransactionCommitted,
    TransactionRolledBack,
    TransactionStarted,
    WorkflowCompleted,
    WorkflowStarted,
)
from core.events.models import DomainEvent
from core.events.snapshot.models import Snapshot

_EVENT_CLASS_BY_TYPE: dict[str, type[DomainEvent]] = {
    "WorkflowStarted": WorkflowStarted,
    "WorkflowCompleted": WorkflowCompleted,
    "AnalysisStarted": AnalysisStarted,
    "AnalysisCompleted": AnalysisCompleted,
    "ReportBuilt": ReportBuilt,
    "ReportExported": ReportExported,
    "ProviderCalled": ProviderCalled,
    "ProviderCompleted": ProviderCompleted,
    "CapabilityExecuted": CapabilityExecuted,
    "TransactionStarted": TransactionStarted,
    "TransactionCommitted": TransactionCommitted,
    "TransactionRolledBack": TransactionRolledBack,
    "DomainEvent": DomainEvent,
}


def event_to_record(event: DomainEvent) -> dict[str, str]:
    """Convert a domain event to SQLite column values."""
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "aggregate_id": event.aggregate_id,
        "occurred_at": event.occurred_at,
        "payload_json": json.dumps(event.payload, ensure_ascii=False),
    }


def record_to_event(row: tuple[Any, ...] | sqlite3.Row) -> DomainEvent:
    """Restore a domain event from a SQLite row."""
    event_id = row["event_id"] if hasattr(row, "keys") else row[1]
    event_type = row["event_type"] if hasattr(row, "keys") else row[2]
    aggregate_id = row["aggregate_id"] if hasattr(row, "keys") else row[3]
    occurred_at = row["occurred_at"] if hasattr(row, "keys") else row[4]
    payload_json = row["payload_json"] if hasattr(row, "keys") else row[5]
    payload = json.loads(payload_json)
    event_cls = _EVENT_CLASS_BY_TYPE.get(event_type, DomainEvent)
    return event_cls(
        event_id=event_id,
        event_type=event_type,
        aggregate_id=aggregate_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def snapshot_to_record(snapshot: Snapshot) -> dict[str, str | int]:
    """Convert a snapshot to SQLite column values."""
    return {
        "snapshot_id": snapshot.snapshot_id,
        "aggregate_id": snapshot.aggregate_id,
        "aggregate_type": snapshot.aggregate_type,
        "aggregate_version": snapshot.aggregate_version,
        "created_at": snapshot.created_at,
        "state_json": json.dumps(snapshot.state, ensure_ascii=False),
    }


def record_to_snapshot(row: tuple[Any, ...] | sqlite3.Row) -> Snapshot:
    """Restore a snapshot from a SQLite row."""
    snapshot_id = row["snapshot_id"] if hasattr(row, "keys") else row[1]
    aggregate_id = row["aggregate_id"] if hasattr(row, "keys") else row[2]
    aggregate_type = row["aggregate_type"] if hasattr(row, "keys") else row[3]
    aggregate_version = row["aggregate_version"] if hasattr(row, "keys") else row[4]
    created_at = row["created_at"] if hasattr(row, "keys") else row[5]
    state_json = row["state_json"] if hasattr(row, "keys") else row[6]
    return Snapshot(
        snapshot_id=snapshot_id,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        aggregate_version=int(aggregate_version),
        created_at=created_at,
        state=json.loads(state_json),
    )
