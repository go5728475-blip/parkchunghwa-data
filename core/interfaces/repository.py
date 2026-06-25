"""Repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TEntity = TypeVar("TEntity")
TId = TypeVar("TId")


class IRepository(ABC, Generic[TEntity, TId]):
    """Generic persistence port for aggregate roots."""

    @abstractmethod
    async def get_by_id(self, entity_id: TId) -> TEntity | None:
        """Retrieve an entity by identifier."""

    @abstractmethod
    async def add(self, entity: TEntity) -> None:
        """Persist a new entity."""

    @abstractmethod
    async def update(self, entity: TEntity) -> None:
        """Persist changes to an existing entity."""

    @abstractmethod
    async def delete(self, entity_id: TId) -> None:
        """Remove an entity by identifier."""
