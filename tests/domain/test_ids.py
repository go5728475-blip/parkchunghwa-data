"""Tests for domain identifiers."""

from __future__ import annotations

import pytest

from core.domain.ids import (
    AggregateId,
    EntityId,
    EventId,
    PluginId,
    ProviderId,
    ReportId,
    SessionId,
    TypedId,
    UserId,
)

ID_TYPES: list[type[TypedId]] = [
    EntityId,
    AggregateId,
    EventId,
    SessionId,
    ReportId,
    UserId,
    ProviderId,
    PluginId,
]


@pytest.mark.parametrize("id_type", ID_TYPES)
def test_id_new_generates_uuid_string(id_type: type[TypedId]) -> None:
    identifier = id_type.new()
    assert identifier.value
    assert len(identifier.value) == 36


@pytest.mark.parametrize("id_type", ID_TYPES)
def test_id_equality_by_value(id_type: type[TypedId]) -> None:
    first = id_type(value="same-id")
    second = id_type(value="same-id")
    third = id_type(value="other-id")
    assert first == second
    assert first != third


@pytest.mark.parametrize("id_type", ID_TYPES)
def test_id_str_returns_value(id_type: type[TypedId]) -> None:
    identifier = id_type(value="abc-123")
    assert str(identifier) == "abc-123"


@pytest.mark.parametrize("id_type", ID_TYPES)
def test_id_rejects_empty_value(id_type: type[TypedId]) -> None:
    with pytest.raises(ValueError, match="empty"):
        id_type(value="")


@pytest.mark.parametrize("id_type", ID_TYPES)
def test_id_rejects_blank_value(id_type: type[TypedId]) -> None:
    with pytest.raises(ValueError, match="empty"):
        id_type(value="   ")
