"""CQRS command contract."""

from __future__ import annotations

from dataclasses import dataclass

from core.contracts.base import Contract
from core.contracts.metadata import Metadata


@dataclass(frozen=True, kw_only=True)
class Command(Contract):
    """Base write-side command contract."""

    metadata: Metadata
