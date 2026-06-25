"""Tests for named provider stubs."""

from __future__ import annotations

import pytest

from core.provider.named_stubs import (
    ClaudeStubProvider,
    GeminiStubProvider,
    LocalModelStubProvider,
    OpenAIStubProvider,
)


@pytest.mark.parametrize(
    ("provider_cls", "provider_id", "model", "placeholder"),
    [
        (OpenAIStubProvider, "openai.stub", "gpt-stub", "openai stub placeholder response"),
        (ClaudeStubProvider, "claude.stub", "claude-stub", "claude stub placeholder response"),
        (GeminiStubProvider, "gemini.stub", "gemini-stub", "gemini stub placeholder response"),
        (
            LocalModelStubProvider,
            "local.stub",
            "local-stub",
            "local model stub placeholder response",
        ),
    ],
)
def test_named_stub_provider_metadata_and_generate(
    provider_cls: type,
    provider_id: str,
    model: str,
    placeholder: str,
) -> None:
    provider = provider_cls()
    provider.initialize()

    metadata = provider.metadata()
    assert str(metadata.provider_id) == provider_id
    assert metadata.model == model
    assert metadata.capabilities == ("text.generate",)
    assert metadata.enabled is True
    assert provider.health_check() is True

    result = provider.generate("hello prompt")
    assert placeholder in result
    assert "hello prompt" in result


def test_named_stub_provider_ids() -> None:
    assert str(OpenAIStubProvider.provider_id()) == "openai.stub"
    assert str(ClaudeStubProvider.provider_id()) == "claude.stub"
    assert str(GeminiStubProvider.provider_id()) == "gemini.stub"
    assert str(LocalModelStubProvider.provider_id()) == "local.stub"
