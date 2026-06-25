"""Tests for query bus."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from core.application.query_bus import QueryBus
from core.application.result import Failure, Result, Success
from core.contracts.metadata import Metadata
from core.contracts.query import Query


@dataclass(frozen=True, kw_only=True)
class SampleQuery(Query):
    key: str


def test_query_bus_register_and_execute() -> None:
    bus = QueryBus()

    def handler(query: SampleQuery) -> Result[str]:
        return Result.ok(f"value:{query.key}")

    bus.register(SampleQuery, handler)
    result = bus.execute(
        SampleQuery(metadata=Metadata(correlation_id=uuid4()), key="abc"),
    )

    assert isinstance(result, Success)
    assert result.unwrap() == "value:abc"


def test_query_bus_missing_handler_returns_failure() -> None:
    bus = QueryBus()
    result = bus.execute(
        SampleQuery(metadata=Metadata(correlation_id=uuid4()), key="x"),
    )
    assert isinstance(result, Failure)
    assert result.error.code == "HANDLER_NOT_FOUND"


def test_query_bus_handler_exception_returns_failure() -> None:
    bus = QueryBus()

    def handler(_query: SampleQuery) -> Result[str]:
        msg = "query failed"
        raise RuntimeError(msg)

    bus.register(SampleQuery, handler)
    result = bus.execute(
        SampleQuery(metadata=Metadata(correlation_id=uuid4()), key="x"),
    )
    assert isinstance(result, Failure)
    assert result.error.code == "HANDLER_ERROR"
