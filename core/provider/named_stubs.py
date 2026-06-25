"""Named provider stubs for OpenAI, Claude, Gemini, and local models."""

from __future__ import annotations

from typing import Any

from core.domain.ids import ProviderId
from core.provider.metadata import ProviderMetadata


class _NamedStubProviderBase:
    """Shared placeholder implementation for named provider stubs."""

    def __init__(
        self,
        *,
        provider_id: str,
        name: str,
        model: str,
        placeholder: str,
        enabled: bool = True,
    ) -> None:
        self._provider_id = ProviderId(value=provider_id)
        self._name = name
        self._model = model
        self._placeholder = placeholder
        self._enabled = enabled
        self._initialized = False

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_id=self._provider_id,
            name=self._name,
            version="0.1.0",
            model=self._model,
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
        return f"{self._placeholder}: {prompt}{context_suffix}"


class OpenAIStubProvider(_NamedStubProviderBase):
    """Placeholder provider for OpenAI-style text generation."""

    def __init__(self, enabled: bool = True) -> None:
        super().__init__(
            provider_id="openai.stub",
            name="OpenAI Stub Provider",
            model="gpt-stub",
            placeholder="openai stub placeholder response",
            enabled=enabled,
        )

    @classmethod
    def provider_id(cls) -> ProviderId:
        return ProviderId(value="openai.stub")


class ClaudeStubProvider(_NamedStubProviderBase):
    """Placeholder provider for Claude-style text generation."""

    def __init__(self, enabled: bool = True) -> None:
        super().__init__(
            provider_id="claude.stub",
            name="Claude Stub Provider",
            model="claude-stub",
            placeholder="claude stub placeholder response",
            enabled=enabled,
        )

    @classmethod
    def provider_id(cls) -> ProviderId:
        return ProviderId(value="claude.stub")


class GeminiStubProvider(_NamedStubProviderBase):
    """Placeholder provider for Gemini-style text generation."""

    def __init__(self, enabled: bool = True) -> None:
        super().__init__(
            provider_id="gemini.stub",
            name="Gemini Stub Provider",
            model="gemini-stub",
            placeholder="gemini stub placeholder response",
            enabled=enabled,
        )

    @classmethod
    def provider_id(cls) -> ProviderId:
        return ProviderId(value="gemini.stub")


class LocalModelStubProvider(_NamedStubProviderBase):
    """Placeholder provider for local model text generation."""

    def __init__(self, enabled: bool = True) -> None:
        super().__init__(
            provider_id="local.stub",
            name="Local Model Stub Provider",
            model="local-stub",
            placeholder="local model stub placeholder response",
            enabled=enabled,
        )

    @classmethod
    def provider_id(cls) -> ProviderId:
        return ProviderId(value="local.stub")
