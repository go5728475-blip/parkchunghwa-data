"""Error contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.contracts.base import Contract


@dataclass(frozen=True, kw_only=True)
class ErrorDetail(Contract):
    """Single error detail entry."""

    code: str
    message: str
    field: str | None = None
    context: dict[str, Any] | None = None


@dataclass(frozen=True, kw_only=True)
class Error(Contract):
    """Aggregated error response contract."""

    details: tuple[ErrorDetail, ...]

    @property
    def primary(self) -> ErrorDetail:
        """Return the first error detail."""
        if not self.details:
            msg = "Error contract requires at least one detail."
            raise ValueError(msg)
        return self.details[0]
