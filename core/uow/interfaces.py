"""Unit of work interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from core.uow.context import TransactionContext


class IUnitOfWork(ABC):
    """Port for workflow transaction boundaries."""

    @property
    @abstractmethod
    def context(self) -> TransactionContext:
        """Return the current transaction context."""

    @abstractmethod
    def begin(self) -> None:
        """Start a transaction."""

    @abstractmethod
    def commit(self) -> None:
        """Commit pending changes."""

    @abstractmethod
    def rollback(self) -> None:
        """Roll back pending changes."""

    def __enter__(self) -> IUnitOfWork:
        self.begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
            return
        self.commit()
