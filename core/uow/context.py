"""Transaction context state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TransactionContext:
    """Tracks transaction lifecycle state."""

    active: bool = False
    committed: bool = False
    rolled_back: bool = False
    started_at: str | None = None
    finished_at: str | None = None
