"""Tests for analysis session aggregate."""

from __future__ import annotations

import pytest

from core.domain.events import AnalysisSessionCreated
from core.domain.ids import SessionId, UserId
from core.domain.session import AnalysisSession, SessionStatus
from core.domain.value_objects import BirthData, EngineContext


def _birth_data() -> BirthData:
    return BirthData(year=1992, month=3, day=10, hour=8, minute=0)


def _context(user_id: UserId, session_id: SessionId) -> EngineContext:
    return EngineContext(user_id=user_id, session_id=session_id)


def test_analysis_session_create_records_event() -> None:
    user_id = UserId.new()
    session_id = SessionId.new()
    session = AnalysisSession.create(
        user_id=user_id,
        birth_data=_birth_data(),
        context=_context(user_id, session_id),
    )
    assert session.status == SessionStatus.CREATED
    events = session.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], AnalysisSessionCreated)
    assert events[0].event_type == "AnalysisSessionCreated"


def test_analysis_session_status_transitions() -> None:
    user_id = UserId.new()
    session_id = SessionId.new()
    session = AnalysisSession.create(
        user_id=user_id,
        birth_data=_birth_data(),
        context=_context(user_id, session_id),
    )
    session.pull_events()
    session.mark_running()
    session.mark_completed()
    assert session.status == SessionStatus.COMPLETED


def test_analysis_session_cannot_revert_from_completed() -> None:
    user_id = UserId.new()
    session_id = SessionId.new()
    session = AnalysisSession.create(
        user_id=user_id,
        birth_data=_birth_data(),
        context=_context(user_id, session_id),
    )
    session.pull_events()
    session.mark_running()
    session.mark_completed()
    with pytest.raises(ValueError):
        session.mark_running()


def test_analysis_session_failed_requires_reason() -> None:
    user_id = UserId.new()
    session_id = SessionId.new()
    session = AnalysisSession.create(
        user_id=user_id,
        birth_data=_birth_data(),
        context=_context(user_id, session_id),
    )
    with pytest.raises(ValueError, match="reason"):
        session.mark_failed("")
