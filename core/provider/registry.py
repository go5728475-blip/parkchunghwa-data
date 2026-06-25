"""In-memory provider registry."""

from __future__ import annotations

from core.domain.ids import ProviderId
from core.provider.errors import DuplicateProviderError, ProviderNotFoundError
from core.provider.interface import ProviderInterface


class ProviderRegistry:
    """Stores provider instances keyed by provider id."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderInterface] = {}

    def register(self, provider: ProviderInterface) -> None:
        """Register a provider instance."""
        provider_id = str(provider.metadata().provider_id)
        if provider_id in self._providers:
            msg = f"Provider already registered: {provider_id}"
            raise DuplicateProviderError(msg)
        self._providers[provider_id] = provider

    def unregister(self, provider_id: ProviderId) -> None:
        """Remove a provider by id."""
        key = str(provider_id)
        if key not in self._providers:
            msg = f"Provider not found: {provider_id}"
            raise ProviderNotFoundError(msg)
        del self._providers[key]

    def get(self, provider_id: ProviderId) -> ProviderInterface:
        """Return a registered provider."""
        provider = self._providers.get(str(provider_id))
        if provider is None:
            msg = f"Provider not found: {provider_id}"
            raise ProviderNotFoundError(msg)
        return provider

    def list(self) -> list[ProviderInterface]:
        """Return all registered providers."""
        return list(self._providers.values())

    def list_enabled(self) -> list[ProviderInterface]:
        """Return registered providers marked as enabled."""
        return [
            provider
            for provider in self._providers.values()
            if provider.metadata().enabled
        ]

    def exists(self, provider_id: ProviderId) -> bool:
        """Return whether a provider id is registered."""
        return str(provider_id) in self._providers
