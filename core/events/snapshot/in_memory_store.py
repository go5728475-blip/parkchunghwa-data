"""In-memory snapshot store."""

from __future__ import annotations

from core.events.snapshot.interfaces import ISnapshotStore
from core.events.snapshot.models import Snapshot


class InMemorySnapshotStore(ISnapshotStore):
    """In-memory snapshot store keyed by aggregate."""

    def __init__(self) -> None:
        self._snapshots: list[Snapshot] = []

    def save(self, snapshot: Snapshot) -> None:
        self._snapshots.append(snapshot)

    def get_latest(self, aggregate_id: str) -> Snapshot | None:
        matching = [
            snapshot
            for snapshot in self._snapshots
            if snapshot.aggregate_id == aggregate_id
        ]
        if not matching:
            return None
        return max(matching, key=lambda item: item.aggregate_version)

    def list(self) -> tuple[Snapshot, ...]:
        return tuple(self._snapshots)

    def clear(self) -> None:
        self._snapshots.clear()
