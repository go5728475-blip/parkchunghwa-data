"""Transactional wrappers for in-memory stores."""

from __future__ import annotations

from core.events.models import DomainEvent
from core.events.snapshot.interfaces import ISnapshotStore
from core.events.snapshot.models import Snapshot
from core.events.store.interfaces import EventNotFoundError, IEventStore


class TransactionalEventStore(IEventStore):
    """Buffers event writes until a transaction commits."""

    def __init__(self, delegate: IEventStore) -> None:
        self._delegate = delegate
        self._buffering = False
        self._buffer: list[DomainEvent] = []

    @property
    def delegate(self) -> IEventStore:
        return self._delegate

    def begin_buffering(self) -> None:
        self._buffering = True
        self._buffer.clear()

    def commit_buffer(self) -> None:
        if self._buffer:
            self._delegate.append_many(self._buffer)
        self._buffer.clear()
        self._buffering = False

    def rollback_buffer(self) -> None:
        self._buffer.clear()
        self._buffering = False

    def append(self, event: DomainEvent) -> None:
        if self._buffering:
            self._buffer.append(event)
            return
        self._delegate.append(event)

    def append_many(self, events: tuple[DomainEvent, ...] | list[DomainEvent]) -> None:
        for event in events:
            self.append(event)

    def get(self, event_id: str) -> DomainEvent:
        for event in self._buffer:
            if event.event_id == event_id:
                return event
        return self._delegate.get(event_id)

    def list(self) -> tuple[DomainEvent, ...]:
        return self._delegate.list() + tuple(self._buffer)

    def list_by_aggregate(self, aggregate_id: str) -> tuple[DomainEvent, ...]:
        buffered = tuple(
            event for event in self._buffer if event.aggregate_id == aggregate_id
        )
        return self._delegate.list_by_aggregate(aggregate_id) + buffered

    def clear(self) -> None:
        self._buffer.clear()
        self._delegate.clear()


class TransactionalSnapshotStore(ISnapshotStore):
    """Buffers snapshot writes until a transaction commits."""

    def __init__(self, delegate: ISnapshotStore) -> None:
        self._delegate = delegate
        self._buffering = False
        self._buffer: list[Snapshot] = []

    @property
    def delegate(self) -> ISnapshotStore:
        return self._delegate

    def begin_buffering(self) -> None:
        self._buffering = True
        self._buffer.clear()

    def commit_buffer(self) -> None:
        for snapshot in self._buffer:
            self._delegate.save(snapshot)
        self._buffer.clear()
        self._buffering = False

    def rollback_buffer(self) -> None:
        self._buffer.clear()
        self._buffering = False

    def save(self, snapshot: Snapshot) -> None:
        if self._buffering:
            self._buffer.append(snapshot)
            return
        self._delegate.save(snapshot)

    def get_latest(self, aggregate_id: str) -> Snapshot | None:
        buffered = [
            snapshot
            for snapshot in self._buffer
            if snapshot.aggregate_id == aggregate_id
        ]
        latest_buffered = (
            max(buffered, key=lambda item: item.aggregate_version)
            if buffered
            else None
        )
        latest_delegate = self._delegate.get_latest(aggregate_id)
        if latest_buffered is None:
            return latest_delegate
        if latest_delegate is None:
            return latest_buffered
        if latest_buffered.aggregate_version >= latest_delegate.aggregate_version:
            return latest_buffered
        return latest_delegate

    def list(self) -> tuple[Snapshot, ...]:
        return self._delegate.list() + tuple(self._buffer)

    def clear(self) -> None:
        self._buffer.clear()
        self._delegate.clear()
