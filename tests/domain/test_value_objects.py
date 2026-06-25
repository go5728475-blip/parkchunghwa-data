"""Tests for domain value objects."""

from __future__ import annotations

import pytest

from core.domain.ids import SessionId, UserId
from core.domain.value_objects import (
    BirthData,
    ConfidenceScore,
    EngineContext,
    ExplanationTrace,
    ReportSection,
)


def test_confidence_score_accepts_valid_range() -> None:
    score = ConfidenceScore(value=0.75)
    assert score.value == 0.75


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_confidence_score_rejects_out_of_range(value: float) -> None:
    with pytest.raises(ValueError, match="0.0 and 1.0"):
        ConfidenceScore(value=value)


def test_birth_data_accepts_valid_values() -> None:
    birth = BirthData(year=1990, month=6, day=15, hour=9, minute=30)
    assert birth.year == 1990


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("year", {"year": 0, "month": 1, "day": 1, "hour": 0, "minute": 0}),
        ("month", {"year": 2000, "month": 13, "day": 1, "hour": 0, "minute": 0}),
        ("day", {"year": 2000, "month": 1, "day": 32, "hour": 0, "minute": 0}),
        ("hour", {"year": 2000, "month": 1, "day": 1, "hour": 24, "minute": 0}),
        ("minute", {"year": 2000, "month": 1, "day": 1, "hour": 0, "minute": 60}),
    ],
)
def test_birth_data_rejects_invalid_values(field_name: str, kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError, match=field_name):
        BirthData(**kwargs)


def test_engine_context_holds_ids_and_metadata() -> None:
    user_id = UserId.new()
    session_id = SessionId.new()
    context = EngineContext(
        user_id=user_id,
        session_id=session_id,
        metadata={"locale": "ko"},
    )
    assert context.user_id == user_id
    assert context.metadata["locale"] == "ko"


def test_explanation_trace_requires_steps() -> None:
    with pytest.raises(ValueError, match="reason_steps"):
        ExplanationTrace(reason_steps=())


def test_report_section_requires_title_and_content() -> None:
    with pytest.raises(ValueError, match="title"):
        ReportSection(
            title=" ",
            content="body",
            confidence=ConfidenceScore(value=0.5),
        )
