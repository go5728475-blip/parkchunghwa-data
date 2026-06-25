"""Tests for stub plugin."""

from __future__ import annotations

from core.plugin.stub import StubPlugin


def test_stub_plugin_execute_returns_placeholder() -> None:
    plugin = StubPlugin()
    plugin.initialize()

    result = plugin.execute({"key": "value"})

    assert result["result"] == "stub placeholder"
    assert "stub.analysis" in plugin.metadata().capabilities
