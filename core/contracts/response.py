"""Response contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from core.contracts.base import Contract
from core.contracts.metadata import Metadata

TData = TypeVar("TData")


@dataclass(frozen=True, kw_only=True)
class Response(Contract, Generic[TData]):
    """Base outbound response contract."""

    metadata: Metadata
    data: TData
