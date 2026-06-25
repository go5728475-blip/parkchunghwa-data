"""Tests for provider catalog query."""

from __future__ import annotations

from uuid import uuid4

from core.application.queries import ListProviders
from core.application.result import Success
from core.bootstrap.bootstrap import Bootstrap
from core.contracts.metadata import Metadata
from core.provider.named_stubs import (
    ClaudeStubProvider,
    GeminiStubProvider,
    LocalModelStubProvider,
    OpenAIStubProvider,
)
from core.provider.stub import StubProvider


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


EXPECTED_PROVIDER_IDS = {
    "stub.provider",
    "openai.stub",
    "claude.stub",
    "gemini.stub",
    "local.stub",
}


def test_list_providers_query_success() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.query_bus().execute(
        ListProviders(metadata=_metadata()),
    )

    assert isinstance(result, Success)
    providers = result.unwrap()
    provider_ids = {str(item.provider_id) for item in providers}
    assert provider_ids == EXPECTED_PROVIDER_IDS
    assert len(providers) == 5


def test_list_providers_includes_required_metadata_fields() -> None:
    bootstrap = Bootstrap().build()
    providers = bootstrap.query_bus().execute(
        ListProviders(metadata=_metadata()),
    ).unwrap()

    for item in providers:
        assert item.name
        assert item.model
        assert "text.generate" in item.capabilities
        assert item.enabled is True


def test_list_providers_includes_named_stubs() -> None:
    bootstrap = Bootstrap().build()
    providers = bootstrap.query_bus().execute(
        ListProviders(metadata=_metadata()),
    ).unwrap()

    provider_ids = {str(item.provider_id) for item in providers}
    assert OpenAIStubProvider.provider_id().value in provider_ids
    assert ClaudeStubProvider.provider_id().value in provider_ids
    assert GeminiStubProvider.provider_id().value in provider_ids
    assert LocalModelStubProvider.provider_id().value in provider_ids
    assert StubProvider.provider_id().value in provider_ids


def test_bootstrap_registers_five_providers() -> None:
    bootstrap = Bootstrap().build()
    manager = bootstrap.provider_manager()
    providers = manager.registry.list()

    assert len(providers) == 5
    provider_ids = {str(provider.metadata().provider_id) for provider in providers}
    assert provider_ids == EXPECTED_PROVIDER_IDS
