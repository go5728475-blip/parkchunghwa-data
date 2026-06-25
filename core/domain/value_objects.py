"""Domain value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.domain.ids import SessionId, UserId


@dataclass(frozen=True, kw_only=True)
class ConfidenceScore:
    """Normalized confidence value between 0.0 and 1.0 inclusive."""

    value: float

    def __post_init__(self) -> None:
        if self.value < 0.0 or self.value > 1.0:
            msg = "ConfidenceScore must be between 0.0 and 1.0."
            raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class BirthData:
    """Birth datetime components for analysis input."""

    year: int
    month: int
    day: int
    hour: int
    minute: int

    def __post_init__(self) -> None:
        if self.year < 1:
            raise ValueError("BirthData.year must be positive.")
        if not 1 <= self.month <= 12:
            raise ValueError("BirthData.month must be between 1 and 12.")
        if not 1 <= self.day <= 31:
            raise ValueError("BirthData.day must be between 1 and 31.")
        if not 0 <= self.hour <= 23:
            raise ValueError("BirthData.hour must be between 0 and 23.")
        if not 0 <= self.minute <= 59:
            raise ValueError("BirthData.minute must be between 0 and 59.")


@dataclass(frozen=True, kw_only=True)
class EngineContext:
    """Execution context for engine operations."""

    user_id: UserId
    session_id: SessionId
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@dataclass(frozen=True, kw_only=True)
class ExplanationTrace:
    """Stepwise explanation trace for explainable output."""

    reason_steps: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.reason_steps:
            raise ValueError("ExplanationTrace.reason_steps cannot be empty.")
        if any(not step.strip() for step in self.reason_steps):
            raise ValueError("ExplanationTrace.reason_steps cannot contain blank steps.")


@dataclass(frozen=True, kw_only=True)
class ReportSection:
    """Single section within a generated report."""

    title: str
    content: str
    confidence: ConfidenceScore
    section_id: str | None = None
    explanation_id: str | None = None
    generated_by: str | None = None
    reasoning: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)
    enriched_from_section_id: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("ReportSection.title cannot be empty.")
        if not self.content.strip():
            raise ValueError("ReportSection.content cannot be empty.")
        if self.reasoning is None:
            object.__setattr__(self, "reasoning", ())
        if self.evidence is None:
            object.__setattr__(self, "evidence", ())
