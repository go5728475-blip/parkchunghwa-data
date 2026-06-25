"""Snapshot models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, kw_only=True)
class Snapshot:
    """Generic aggregate snapshot for event-sourced recovery."""

    snapshot_id: str = field(default_factory=lambda: str(uuid4()))
    aggregate_id: str
    aggregate_type: str
    aggregate_version: int
    created_at: str = field(default_factory=_utc_timestamp)
    state: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.aggregate_id.strip():
            msg = "Snapshot aggregate_id cannot be empty."
            raise ValueError(msg)
        if not self.aggregate_type.strip():
            msg = "Snapshot aggregate_type cannot be empty."
            raise ValueError(msg)
        if self.aggregate_version < 0:
            msg = "Snapshot aggregate_version cannot be negative."
            raise ValueError(msg)
        if self.state is None:
            object.__setattr__(self, "state", {})
