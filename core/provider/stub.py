"""Stub provider for development and testing."""

from __future__ import annotations

from typing import Any

from core.domain.ids import ProviderId
from core.provider.metadata import ProviderMetadata

_STUB_PROVIDER_ID = ProviderId(value="stub.provider")
_STUB_PLACEHOLDER = "stub provider placeholder response"


class StubProvider:
    """Placeholder provider without external API integration."""

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._initialized = False

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_id=_STUB_PROVIDER_ID,
            name="Stub Provider",
            version="0.1.0",
            model="stub-model",
            capabilities=("text.generate",),
            enabled=self._enabled,
        )

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def health_check(self) -> bool:
        return self._initialized or not self._enabled

    def generate(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        context_suffix = ""
        if context:
            context_suffix = f" | context_keys={sorted(context.keys())}"
        return f"{_STUB_PLACEHOLDER}: {prompt}{context_suffix}"

    @classmethod
    def provider_id(cls) -> ProviderId:
        return _STUB_PROVIDER_ID
