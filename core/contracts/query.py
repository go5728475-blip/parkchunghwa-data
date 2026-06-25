"""CQRS query contract."""

from __future__ import annotations

from dataclasses import dataclass

from core.contracts.base import Contract
from core.contracts.metadata import Metadata
from core.contracts.pagination import Pagination


@dataclass(frozen=True, kw_only=True)
class Query(Contract):
    """Base read-side query contract."""

    metadata: Metadata
    pagination: Pagination | None = None
