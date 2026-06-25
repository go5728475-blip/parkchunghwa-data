"""Strongly typed domain identifiers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar
from uuid import uuid4

TId = TypeVar("TId", bound="TypedId")


@dataclass(frozen=True)
class TypedId:
    """Base immutable identifier value object."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            msg = "ID value cannot be empty."
            raise ValueError(msg)

    @classmethod
    def new(cls: type[TId]) -> TId:
        """Create a new identifier using UUID4."""
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EntityId(TypedId):
    """Identifier for generic entities."""


@dataclass(frozen=True)
class AggregateId(TypedId):
    """Identifier for aggregate roots."""


@dataclass(frozen=True)
class EventId(TypedId):
    """Identifier for domain events."""


@dataclass(frozen=True)
class SessionId(TypedId):
    """Identifier for analysis sessions."""


@dataclass(frozen=True)
class ReportId(TypedId):
    """Identifier for reports."""


@dataclass(frozen=True)
class UserId(TypedId):
    """Identifier for users."""


@dataclass(frozen=True)
class ProviderId(TypedId):
    """Identifier for external providers."""


@dataclass(frozen=True)
class PluginId(TypedId):
    """Identifier for plugins."""


@dataclass(frozen=True)
class SectionId(TypedId):
    """Identifier for analysis sections."""


@dataclass(frozen=True)
class ExplanationId(TypedId):
    """Identifier for analysis explanations."""


@dataclass(frozen=True)
class WorkflowId(TypedId):
    """Identifier for workflow executions."""
