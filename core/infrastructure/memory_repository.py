"""In-memory repository implementations."""

from __future__ import annotations

from typing import Generic, TypeVar

from core.domain.report import Report
from core.domain.session import AnalysisSession

TEntity = TypeVar("TEntity")


class InMemoryRepository(Generic[TEntity]):
    """Dict-backed generic in-memory repository."""

    def __init__(self) -> None:
        self._storage: dict[str, TEntity] = {}

    def save(self, entity: TEntity) -> None:
        """Persist or update an entity keyed by its id."""
        self._storage[str(entity.id)] = entity  # type: ignore[attr-defined]

    def get(self, entity_id: object) -> TEntity | None:
        """Retrieve an entity by id, or None if missing."""
        return self._storage.get(str(entity_id))

    def list(self) -> list[TEntity]:
        """Return all stored entities."""
        return list(self._storage.values())

    def delete(self, entity_id: object) -> None:
        """Remove an entity by id; no-op when missing."""
        self._storage.pop(str(entity_id), None)

    def exists(self, entity_id: object) -> bool:
        """Return whether an entity with the given id exists."""
        return str(entity_id) in self._storage


class InMemoryAnalysisSessionRepository(InMemoryRepository[AnalysisSession]):
    """In-memory repository for analysis session aggregates."""


class InMemoryReportRepository(InMemoryRepository[Report]):
    """In-memory repository for report aggregates."""
