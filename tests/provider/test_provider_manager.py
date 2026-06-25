"""Tests for provider manager."""

from __future__ import annotations

import pytest

from core.provider.errors import ProviderGenerationError, ProviderNotFoundError
from core.provider.manager import ProviderManager
from core.provider.registry import ProviderRegistry
from core.provider.stub import StubProvider


def test_provider_manager_initialize_and_shutdown_all() -> None:
    registry = ProviderRegistry()
    manager = ProviderManager(registry)
    provider = StubProvider()

    registry.register(provider)
    manager.initialize_all()
    assert provider.health_check()

    manager.shutdown_all()
    assert not provider._initialized  # noqa: SLF001


def test_provider_manager_generate_success() -> None:
    registry = ProviderRegistry()
    manager = ProviderManager(registry)
    registry.register(StubProvider())
    manager.initialize_all()

    result = manager.generate(StubProvider.provider_id(), "hello prompt")

    assert "stub provider placeholder response" in result
    assert "hello prompt" in result


def test_provider_manager_generate_disabled_provider_fails() -> None:
    registry = ProviderRegistry()
    manager = ProviderManager(registry)
    registry.register(StubProvider(enabled=False))

    with pytest.raises(ProviderGenerationError, match="disabled"):
        manager.generate(StubProvider.provider_id(), "prompt")


def test_provider_manager_generate_missing_provider_fails() -> None:
    manager = ProviderManager(ProviderRegistry())

    with pytest.raises(ProviderNotFoundError):
        manager.generate(StubProvider.provider_id(), "prompt")
