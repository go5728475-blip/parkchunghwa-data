"""Tests for capability catalog query."""

from __future__ import annotations

from uuid import uuid4

from core.application.queries import ListCapabilities
from core.application.result import Success
from core.bootstrap.bootstrap import Bootstrap
from core.contracts.metadata import Metadata


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


EXPECTED_CAPABILITIES = {
    "stub.analysis",
    "master_lock.analysis",
    "wealth.analysis",
    "career.analysis",
    "relationship.analysis",
}


def test_list_capabilities_query_success() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.query_bus().execute(
        ListCapabilities(metadata=_metadata()),
    )

    assert isinstance(result, Success)
    capabilities = set(result.unwrap())
    assert capabilities == EXPECTED_CAPABILITIES


def test_list_capabilities_includes_all_registered_analysis_capabilities() -> None:
    bootstrap = Bootstrap().build()
    capabilities = bootstrap.query_bus().execute(
        ListCapabilities(metadata=_metadata()),
    ).unwrap()

    assert len(capabilities) == 5
    for capability in EXPECTED_CAPABILITIES:
        assert capability in capabilities
