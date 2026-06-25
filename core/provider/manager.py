"""Provider lifecycle and generation manager."""

from __future__ import annotations

from typing import Any

from core.domain.ids import ProviderId
from core.provider.errors import ProviderGenerationError, ProviderNotFoundError
from core.provider.registry import ProviderRegistry


class ProviderManager:
    """Coordinates provider initialization, generation, and health checks."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    def initialize_all(self) -> None:
        """Initialize all enabled providers."""
        for provider in self._registry.list_enabled():
            provider.initialize()

    def shutdown_all(self) -> None:
        """Shut down all registered providers."""
        for provider in self._registry.list():
            provider.shutdown()

    def generate(
        self,
        provider_id: ProviderId,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Generate text through a provider by id."""
        if not self._registry.exists(provider_id):
            msg = f"Provider not found: {provider_id}"
            raise ProviderNotFoundError(msg)

        provider = self._registry.get(provider_id)
        if not provider.metadata().enabled:
            msg = f"Provider is disabled: {provider_id}"
            raise ProviderGenerationError(msg)

        try:
            return provider.generate(prompt, context)
        except ProviderGenerationError:
            raise
        except Exception as exc:  # noqa: BLE001
            msg = f"Provider generation failed: {provider_id}"
            raise ProviderGenerationError(msg) from exc

    def health_check_all(self) -> dict[str, bool]:
        """Run health checks for all registered providers."""
        return {
            str(provider.metadata().provider_id): provider.health_check()
            for provider in self._registry.list()
        }
