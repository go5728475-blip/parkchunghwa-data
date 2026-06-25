"""Metadata contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.contracts.base import Contract


@dataclass(frozen=True, kw_only=True)
class Metadata(Contract):
    """Cross-cutting metadata attached to requests and responses."""

    correlation_id: UUID
    causation_id: UUID | None = None
    timestamp: datetime | None = None
    source: str | None = None
