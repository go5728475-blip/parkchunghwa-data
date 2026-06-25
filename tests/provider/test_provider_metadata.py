"""Tests for provider metadata."""

from __future__ import annotations

import pytest

from core.domain.ids import ProviderId
from core.provider.metadata import ProviderMetadata


def test_provider_metadata_is_immutable() -> None:
    metadata = ProviderMetadata(
        provider_id=ProviderId(value="test.provider"),
        name="Test Provider",
        version="1.0.0",
        model="test-model",
        capabilities=("text.generate",),
        enabled=True,
    )

    with pytest.raises(AttributeError):
        metadata.name = "Changed"  # type: ignore[misc]


def test_provider_metadata_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name"):
        ProviderMetadata(
            provider_id=ProviderId(value="bad.provider"),
            name=" ",
            version="1.0.0",
            model="model",
        )
