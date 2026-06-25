"""Query bus for executing application queries."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.application.result import Result, ResultValue


class QueryBus:
    """Routes queries to registered handlers by query type."""

    def __init__(self) -> None:
        self._handlers: dict[type[Any], Callable[[Any], ResultValue[Any]]] = {}

    def register(
        self,
        query_type: type[Any],
        handler: Callable[[Any], ResultValue[Any]],
    ) -> None:
        """Register a handler for a query type."""
        self._handlers[query_type] = handler

    def execute(self, query: Any) -> ResultValue[Any]:
        """Execute a query through its handler."""
        handler = self._handlers.get(type(query))
        if handler is None:
            return Result.fail(
                code="HANDLER_NOT_FOUND",
                message=f"No handler registered for {type(query).__name__}.",
            )
        try:
            return handler(query)
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="HANDLER_ERROR",
                message=str(exc),
            )
