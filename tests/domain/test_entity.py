"""Tests for entity base class."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.domain.entity import Entity
from core.domain.ids import EntityId


def test_entity_touch_updates_updated_at() -> None:
    entity = Entity(id=EntityId.new())
    original_updated_at = entity.updated_at
    past = datetime.now(UTC) - timedelta(seconds=1)
    entity.updated_at = past
    entity.touch()
    assert entity.updated_at > past
    assert entity.created_at <= entity.updated_at
    assert original_updated_at <= entity.updated_at or entity.updated_at > past
