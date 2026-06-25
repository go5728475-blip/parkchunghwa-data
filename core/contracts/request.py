"""Request contract."""

from __future__ import annotations

from dataclasses import dataclass

from core.contracts.base import Contract
from core.contracts.metadata import Metadata


@dataclass(frozen=True, kw_only=True)
class Request(Contract):
    """Base inbound request contract."""

    metadata: Metadata
