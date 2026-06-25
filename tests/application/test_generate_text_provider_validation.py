"""Tests for GenerateText provider pre-validation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.application.command_bus import CommandBus
from core.application.commands import GenerateText
from core.application.handlers import GenerateTextCommandHandler
from core.application.result import Failure, Success
from core.application.use_cases import GenerateTextUseCase
from core.bootstrap.bootstrap import Bootstrap
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId
from core.provider.manager import ProviderManager
from core.provider.named_stubs import OpenAIStubProvider
from core.provider.registry import ProviderRegistry
from core.provider.stub import StubProvider


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _generate_text_command(
    provider_id: ProviderId,
    prompt: str = "hello prompt",
) -> GenerateText:
    return GenerateText(
        metadata=_metadata(),
        provider_id=provider_id,
        prompt=prompt,
    )


def test_generate_text_valid_provider_success() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _generate_text_command(OpenAIStubProvider.provider_id()),
    )

    assert isinstance(result, Success)
    assert "openai stub placeholder response" in result.unwrap()


def test_generate_text_missing_provider_failure() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _generate_text_command(ProviderId(value="missing.provider")),
    )

    assert isinstance(result, Failure)
    error = result.unwrap_error()
    assert error.code == "PROVIDER_NOT_FOUND"
    assert "missing.provider" in error.message


def test_generate_text_disabled_provider_failure() -> None:
    registry = ProviderRegistry()
    registry.register(StubProvider(enabled=False))
    provider_manager = ProviderManager(registry)

    bus = CommandBus()
    bus.register(
        GenerateText,
        GenerateTextCommandHandler(GenerateTextUseCase(provider_manager)),
    )

    result = bus.dispatch(_generate_text_command(StubProvider.provider_id()))

    assert isinstance(result, Failure)
    error = result.unwrap_error()
    assert error.code == "PROVIDER_DISABLED"
    assert "stub.provider" in error.message


def test_generate_text_blank_provider_id_validation() -> None:
    with pytest.raises(ValueError, match="empty"):
        ProviderId(value="   ")


def test_generate_text_blank_prompt_validation() -> None:
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        GenerateText(
            metadata=_metadata(),
            provider_id=OpenAIStubProvider.provider_id(),
            prompt="",
        )


def test_generate_text_whitespace_prompt_validation() -> None:
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        GenerateText(
            metadata=_metadata(),
            provider_id=OpenAIStubProvider.provider_id(),
            prompt="   ",
        )
