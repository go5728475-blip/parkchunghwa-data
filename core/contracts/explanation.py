"""Explainable AI (XAI) contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.contracts.base import Contract


@dataclass(frozen=True, kw_only=True)
class Explanation(Contract):
    """Structured explanation payload for transparent AI decisions."""

    summary: str
    factors: tuple[str, ...] = ()
    confidence: float | None = None
    trace: dict[str, Any] | None = None
