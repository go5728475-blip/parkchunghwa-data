"""Pagination contract."""

from __future__ import annotations

from dataclasses import dataclass

from core.contracts.base import Contract


@dataclass(frozen=True, kw_only=True)
class Pagination(Contract):
    """Cursor/page pagination descriptor."""

    page: int
    page_size: int
    total_items: int | None = None

    @property
    def offset(self) -> int:
        """Zero-based offset for the current page."""
        return max(self.page - 1, 0) * self.page_size
