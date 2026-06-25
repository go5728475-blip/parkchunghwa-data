"""Tests for provider bootstrap wiring."""

from __future__ import annotations

from core.bootstrap.bootstrap import Bootstrap, CONTAINER_KEY_PROVIDER_MANAGER
from core.provider.manager import ProviderManager
from core.provider.stub import StubProvider


def test_bootstrap_resolves_provider_manager() -> None:
    bootstrap = Bootstrap().build()
    manager = bootstrap.container().resolve(CONTAINER_KEY_PROVIDER_MANAGER)

    assert isinstance(manager, ProviderManager)
    assert bootstrap.provider_manager() is manager
    assert bootstrap.registry().has_service("provider_manager")
    assert len(manager.registry.list()) == 5
    assert manager.registry.exists(StubProvider.provider_id())

    result = manager.generate(StubProvider.provider_id(), "bootstrap prompt")
    assert "stub provider placeholder response" in result
