"""Command bus for dispatching application commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.application.result import Failure, Result, ResultValue


class CommandBus:
    """Routes commands to registered handlers by command type."""

    def __init__(self) -> None:
        self._handlers: dict[type[Any], Callable[[Any], ResultValue[Any]]] = {}

    def register(
        self,
        command_type: type[Any],
        handler: Callable[[Any], ResultValue[Any]],
    ) -> None:
        """Register a handler for a command type."""
        self._handlers[command_type] = handler

    def dispatch(self, command: Any) -> ResultValue[Any]:
        """Dispatch a command to its handler."""
        handler = self._handlers.get(type(command))
        if handler is None:
            return Result.fail(
                code="HANDLER_NOT_FOUND",
                message=f"No handler registered for {type(command).__name__}.",
            )
        try:
            return handler(command)
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code="HANDLER_ERROR",
                message=str(exc),
            )
