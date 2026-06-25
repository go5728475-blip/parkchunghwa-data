"""Tests for in-memory repositories."""

from __future__ import annotations

from core.domain.entity import Entity
from core.domain.ids import EntityId, SessionId, UserId
from core.domain.report import Report
from core.domain.session import AnalysisSession
from core.domain.value_objects import BirthData, EngineContext
from core.infrastructure.memory_repository import (
    InMemoryAnalysisSessionRepository,
    InMemoryReportRepository,
    InMemoryRepository,
)


def _session() -> AnalysisSession:
    user_id = UserId.new()
    session_id = SessionId.new()
    return AnalysisSession.create(
        user_id=user_id,
        birth_data=BirthData(year=1990, month=1, day=1, hour=0, minute=0),
        context=EngineContext(user_id=user_id, session_id=session_id),
    )


def test_repository_save_get_list_delete_exists() -> None:
    repo: InMemoryRepository[Entity] = InMemoryRepository()
    entity = Entity(id=EntityId.new())

    repo.save(entity)
    assert repo.get(entity.id) is entity
    assert repo.exists(entity.id)
    assert repo.list() == [entity]

    repo.delete(entity.id)
    assert repo.get(entity.id) is None
    assert not repo.exists(entity.id)
    assert repo.list() == []


def test_repository_get_missing_returns_none() -> None:
    repo: InMemoryRepository[Entity] = InMemoryRepository()
    assert repo.get(EntityId.new()) is None


def test_repository_delete_missing_does_not_fail() -> None:
    repo: InMemoryRepository[Entity] = InMemoryRepository()
    repo.delete(EntityId.new())


def test_analysis_session_repository_save_and_get() -> None:
    repo = InMemoryAnalysisSessionRepository()
    session = _session()
    session.pull_events()

    repo.save(session)
    loaded = repo.get(session.session_id)
    assert loaded is session


def test_report_repository_save_and_get() -> None:
    repo = InMemoryReportRepository()
    report = Report.create(session_id=SessionId.new())
    report.pull_events()

    repo.save(report)
    loaded = repo.get(report.report_id)
    assert loaded is report
