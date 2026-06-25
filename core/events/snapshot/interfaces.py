"""Snapshot store interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.events.snapshot.models import Snapshot


class ISnapshotStore(ABC):
    """Port for aggregate snapshot persistence."""

    @abstractmethod
    def save(self, snapshot: Snapshot) -> None:
        """Persist a snapshot."""

    @abstractmethod
    def get_latest(self, aggregate_id: str) -> Snapshot | None:
        """Return the latest snapshot for an aggregate."""

    @abstractmethod
    def list(self) -> tuple[Snapshot, ...]:
        """Return all stored snapshots in save order."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored snapshots."""
