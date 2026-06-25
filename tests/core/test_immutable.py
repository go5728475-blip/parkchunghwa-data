"""Immutability tests for core contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dataclasses import dataclass

from core.contracts import (
    Command,
    Contract,
    Error,
    ErrorDetail,
    Explanation,
    Metadata,
    Pagination,
    Query,
    Request,
    Response,
)


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4(), timestamp=datetime.now(UTC))


@dataclass(frozen=True, kw_only=True)
class _SampleContract(Contract):
    value: str = "immutable"


@pytest.mark.parametrize(
    "instance",
    [
        _SampleContract(),
        Metadata(correlation_id=uuid4()),
        Request(metadata=_metadata()),
        Response(metadata=_metadata(), data={"ok": True}),
        Explanation(summary="because"),
        Pagination(page=1, page_size=10),
        Error(details=(ErrorDetail(code="E001", message="failed"),)),
        Command(metadata=_metadata()),
        Query(metadata=_metadata()),
    ],
)
def test_contract_instances_are_frozen(instance: Contract) -> None:
    fields = list(instance.__dataclass_fields__)
    field_name = fields[0]
    with pytest.raises(FrozenInstanceError):
        setattr(instance, field_name, object())


def test_error_detail_is_frozen() -> None:
    detail = ErrorDetail(code="E001", message="failed")
    with pytest.raises(FrozenInstanceError):
        detail.message = "changed"


def test_pagination_offset_is_derived() -> None:
    pagination = Pagination(page=3, page_size=25)
    assert pagination.offset == 50
