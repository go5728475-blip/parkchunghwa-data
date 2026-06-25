"""Shared unit-of-work helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from core.domain.models import TraceEntry, TraceStep
from core.events.event_types import (
    TransactionCommitted,
    TransactionRolledBack,
    TransactionStarted,
)
from core.events.helpers import publish_event, trace_for_event
from core.events.interfaces import IEventBus
from core.uow.context import TransactionContext


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


class TransactionEventPublisher:
    """Publishes transaction lifecycle events and builds trace entries."""

    def __init__(self, event_bus: IEventBus | None, aggregate_id: str) -> None:
        self._event_bus = event_bus
        self._aggregate_id = aggregate_id
        self.trace_entries: list[TraceEntry] = []

    def publish_started(self) -> None:
        event = publish_event(
            self._event_bus,
            TransactionStarted(
                aggregate_id=self._aggregate_id,
                payload={"aggregate_id": self._aggregate_id},
            ),
        )
        self.trace_entries.append(
            trace_for_event(
                event,
                step=TraceStep.REPORT,
                source="transaction",
                message="Transaction started",
            ),
        )

    def publish_committed(self) -> None:
        event = publish_event(
            self._event_bus,
            TransactionCommitted(
                aggregate_id=self._aggregate_id,
                payload={"aggregate_id": self._aggregate_id},
            ),
        )
        self.trace_entries.append(
            trace_for_event(
                event,
                step=TraceStep.REPORT,
                source="transaction",
                message="Transaction committed",
            ),
        )

    def publish_rolled_back(self, reason: str) -> None:
        event = publish_event(
            self._event_bus,
            TransactionRolledBack(
                aggregate_id=self._aggregate_id,
                payload={"aggregate_id": self._aggregate_id, "reason": reason},
            ),
        )
        self.trace_entries.append(
            trace_for_event(
                event,
                step=TraceStep.REPORT,
                source="transaction",
                message=f"Transaction rolled back: {reason}",
            ),
        )


def mark_started(context: TransactionContext) -> None:
    context.active = True
    context.committed = False
    context.rolled_back = False
    context.started_at = _utc_timestamp()
    context.finished_at = None


def mark_committed(context: TransactionContext) -> None:
    context.active = False
    context.committed = True
    context.rolled_back = False
    context.finished_at = _utc_timestamp()


def mark_rolled_back(context: TransactionContext) -> None:
    context.active = False
    context.committed = False
    context.rolled_back = True
    context.finished_at = _utc_timestamp()
