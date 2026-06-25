"""Tests for GenerateText application command flow."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.application.commands import GenerateText
from core.application.result import Failure, Success
from core.bootstrap.bootstrap import Bootstrap
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId
from core.provider.named_stubs import (
    ClaudeStubProvider,
    GeminiStubProvider,
    LocalModelStubProvider,
    OpenAIStubProvider,
)
from core.provider.stub import StubProvider


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _generate_text_command(
    provider_id: str,
    prompt: str = "hello prompt",
) -> GenerateText:
    return GenerateText(
        metadata=_metadata(),
        provider_id=ProviderId(value=provider_id),
        prompt=prompt,
    )


def test_generate_text_command_dispatch_success() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _generate_text_command("stub.provider"),
    )

    assert isinstance(result, Success)
    text = result.unwrap()
    assert "stub provider placeholder response" in text
    assert "hello prompt" in text


@pytest.mark.parametrize(
    ("provider_id", "placeholder"),
    [
        ("openai.stub", "openai stub placeholder response"),
        ("claude.stub", "claude stub placeholder response"),
        ("gemini.stub", "gemini stub placeholder response"),
        ("local.stub", "local model stub placeholder response"),
    ],
)
def test_generate_text_named_provider_success(provider_id: str, placeholder: str) -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _generate_text_command(provider_id, prompt="named provider prompt"),
    )

    assert isinstance(result, Success)
    text = result.unwrap()
    assert placeholder in text
    assert "named provider prompt" in text


def test_generate_text_missing_provider_failure() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _generate_text_command("missing.provider"),
    )

    assert isinstance(result, Failure)
    error = result.unwrap_error()
    assert error.code == "PROVIDER_NOT_FOUND"
    assert "missing.provider" in error.message


def test_generate_text_empty_prompt_validation() -> None:
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        GenerateText(
            metadata=_metadata(),
            provider_id=StubProvider.provider_id(),
            prompt="",
        )


def test_generate_text_whitespace_prompt_validation() -> None:
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        GenerateText(
            metadata=_metadata(),
            provider_id=OpenAIStubProvider.provider_id(),
            prompt="   ",
        )


def test_named_provider_ids_available_in_bootstrap() -> None:
    bootstrap = Bootstrap().build()
    manager = bootstrap.provider_manager()

    for provider_cls in (
        OpenAIStubProvider,
        ClaudeStubProvider,
        GeminiStubProvider,
        LocalModelStubProvider,
    ):
        assert manager.registry.exists(provider_cls.provider_id())
