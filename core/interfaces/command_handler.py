"""CQRS command handler interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from core.contracts.command import Command

TCommand = TypeVar("TCommand", bound=Command)
TResult = TypeVar("TResult")


class ICommandHandler(ABC, Generic[TCommand, TResult]):
    """Write-side handler for a single command type."""

    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """Execute the command and return a result."""
