"""Tests for stub provider."""

from __future__ import annotations

from core.provider.stub import StubProvider


def test_stub_provider_health_and_generate() -> None:
    provider = StubProvider()
    provider.initialize()

    assert provider.health_check() is True
    assert provider.metadata().model == "stub-model"
    assert "text.generate" in provider.metadata().capabilities

    result = provider.generate("test prompt", {"locale": "ko"})
    assert "stub provider placeholder response" in result
    assert "test prompt" in result
    assert "locale" in result
