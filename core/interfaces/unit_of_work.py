"""Unit of work interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self


class IUnitOfWork(ABC):
    """Transactional boundary for coordinating persistence operations."""

    @abstractmethod
    async def __aenter__(self) -> Self:
        """Begin a unit of work."""

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Complete or roll back a unit of work."""

    @abstractmethod
    async def commit(self) -> None:
        """Commit pending changes."""

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back pending changes."""
