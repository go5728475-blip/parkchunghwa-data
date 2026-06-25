"""Provider interface contract."""

from __future__ import annotations

from typing import Any, Protocol

from core.provider.metadata import ProviderMetadata


class ProviderInterface(Protocol):
    """Contract for external model providers."""

    def metadata(self) -> ProviderMetadata:
        """Return provider metadata."""

    def initialize(self) -> None:
        """Prepare the provider for generation."""

    def shutdown(self) -> None:
        """Release provider resources."""

    def health_check(self) -> bool:
        """Return whether the provider is healthy."""

    def generate(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        """Generate text from a prompt and optional context."""
