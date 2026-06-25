"""Tests for analysis capability stub plugins."""

from __future__ import annotations

import pytest

from core.plugin.analysis_stubs import (
    CareerStubPlugin,
    MasterLockStubPlugin,
    RelationshipStubPlugin,
    WealthStubPlugin,
)


@pytest.mark.parametrize(
    ("plugin_cls", "plugin_id", "capability", "placeholder"),
    [
        (MasterLockStubPlugin, "master_lock.stub", "master_lock.analysis", "master lock placeholder"),
        (WealthStubPlugin, "wealth.stub", "wealth.analysis", "wealth placeholder"),
        (CareerStubPlugin, "career.stub", "career.analysis", "career placeholder"),
        (RelationshipStubPlugin, "relationship.stub", "relationship.analysis", "relationship placeholder"),
    ],
)
def test_analysis_stub_plugin_metadata_and_execute(
    plugin_cls: type,
    plugin_id: str,
    capability: str,
    placeholder: str,
) -> None:
    plugin = plugin_cls()
    plugin.initialize()

    metadata = plugin.metadata()
    assert str(metadata.plugin_id) == plugin_id
    assert capability in metadata.capabilities
    assert plugin.health_check() is True

    result = plugin.execute({"sample": True})
    assert result["result"] == placeholder
    assert result["capability"] == capability
    assert result["plugin_id"] == plugin_id
