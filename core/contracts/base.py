"""Immutable contract base types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, kw_only=True)
class Contract:
    """Base immutable contract for all domain data transfer objects."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize contract to a plain dictionary."""
        from dataclasses import asdict

        return asdict(self)
