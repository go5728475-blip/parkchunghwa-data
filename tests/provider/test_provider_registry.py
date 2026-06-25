"""Tests for provider registry."""

from __future__ import annotations

import pytest

from core.provider.errors import DuplicateProviderError, ProviderNotFoundError
from core.provider.registry import ProviderRegistry
from core.provider.stub import StubProvider


def test_provider_registry_register_get_list_unregister() -> None:
    registry = ProviderRegistry()
    provider = StubProvider()

    registry.register(provider)
    assert registry.exists(StubProvider.provider_id())
    assert registry.get(StubProvider.provider_id()) is provider
    assert registry.list() == [provider]
    assert registry.list_enabled() == [provider]

    registry.unregister(StubProvider.provider_id())
    assert not registry.exists(StubProvider.provider_id())


def test_provider_registry_duplicate_register_fails() -> None:
    registry = ProviderRegistry()
    registry.register(StubProvider())

    with pytest.raises(DuplicateProviderError):
        registry.register(StubProvider())


def test_provider_registry_list_enabled_excludes_disabled() -> None:
    registry = ProviderRegistry()
    registry.register(StubProvider(enabled=False))

    assert registry.list()
    assert registry.list_enabled() == []
