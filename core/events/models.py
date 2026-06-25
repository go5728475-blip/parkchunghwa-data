"""Domain event models for the event bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Common parent for all bus-published domain events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    aggregate_id: str = ""
    occurred_at: str = field(default_factory=_utc_timestamp)
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_type:
            object.__setattr__(self, "event_type", self.__class__.__name__)
        if self.payload is None:
            object.__setattr__(self, "payload", {})
