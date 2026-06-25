"""CQRS query handler interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from core.contracts.query import Query

TQuery = TypeVar("TQuery", bound=Query)
TResult = TypeVar("TResult")


class IQueryHandler(ABC, Generic[TQuery, TResult]):
    """Read-side handler for a single query type."""

    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """Execute the query and return a result."""
