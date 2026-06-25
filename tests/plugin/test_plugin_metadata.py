"""Tests for plugin metadata."""

from __future__ import annotations

import pytest

from core.domain.ids import PluginId
from core.plugin.metadata import PluginMetadata


def test_plugin_metadata_is_immutable() -> None:
    metadata = PluginMetadata(
        plugin_id=PluginId(value="test.plugin"),
        name="Test Plugin",
        version="1.0.0",
        description="Test description",
        capabilities=("analysis",),
        dependencies=("core",),
        enabled=True,
    )

    with pytest.raises(AttributeError):
        metadata.name = "Changed"  # type: ignore[misc]


def test_plugin_metadata_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name"):
        PluginMetadata(
            plugin_id=PluginId(value="bad.plugin"),
            name=" ",
            version="1.0.0",
            description="desc",
        )
