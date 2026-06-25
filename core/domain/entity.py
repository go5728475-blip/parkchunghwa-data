"""Entity base class."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from core.domain.ids import EntityId


@dataclass
class Entity:
    """Mutable entity with identity and audit timestamps."""

    id: EntityId
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def touch(self) -> None:
        """Update the last-modified timestamp."""
        self.updated_at = datetime.now(UTC)
