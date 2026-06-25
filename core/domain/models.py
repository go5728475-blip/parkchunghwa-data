"""Analysis result domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from core.domain.ids import ExplanationId, SectionId


class SectionSource(StrEnum):
    """Origin of an analysis section."""

    PLUGIN = "PLUGIN"
    PROVIDER = "PROVIDER"


class GeneratedBy(StrEnum):
    """Origin of an analysis explanation."""

    PLUGIN = "PLUGIN"
    PROVIDER = "PROVIDER"


class TraceStep(StrEnum):
    """Pipeline step recorded in analysis trace."""

    PLUGIN = "PLUGIN"
    PROVIDER = "PROVIDER"
    REPORT = "REPORT"


@dataclass(frozen=True, kw_only=True)
class AnalysisExplanation:
    """Explainable metadata for an analysis section."""

    explanation_id: ExplanationId
    section_id: SectionId
    confidence: float
    reasoning: tuple[str, ...]
    evidence: tuple[str, ...]
    generated_by: GeneratedBy

    def __post_init__(self) -> None:
        if self.confidence < 0.0 or self.confidence > 1.0:
            msg = "Confidence must be between 0.0 and 1.0."
            raise ValueError(msg)
        if not self.reasoning:
            msg = "Reasoning cannot be empty."
            raise ValueError(msg)
        if not self.evidence:
            msg = "Evidence cannot be empty."
            raise ValueError(msg)
        if any(not step.strip() for step in self.reasoning):
            msg = "Reasoning cannot contain blank steps."
            raise ValueError(msg)
        if any(not item.strip() for item in self.evidence):
            msg = "Evidence cannot contain blank items."
            raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class TraceEntry:
    """Structured trace entry for analysis pipeline execution."""

    step: TraceStep
    source: str
    timestamp: str
    message: str
    event_id: str | None = None
    event_type: str | None = None
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            msg = "Trace source cannot be empty."
            raise ValueError(msg)
        if not self.timestamp.strip():
            msg = "Trace timestamp cannot be empty."
            raise ValueError(msg)
        if not self.message.strip():
            msg = "Trace message cannot be empty."
            raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class AnalysisSection:
    """Canonical analysis output section."""

    section_id: SectionId
    capability: str
    title: str
    content: str
    source: SectionSource
    explanation: AnalysisExplanation
    enriched_from_section_id: SectionId | None = None

    def __post_init__(self) -> None:
        if not self.capability.strip():
            msg = "Capability cannot be empty."
            raise ValueError(msg)
        if not self.title.strip():
            msg = "Title cannot be empty."
            raise ValueError(msg)
        if not self.content.strip():
            msg = "Content cannot be empty."
            raise ValueError(msg)
        if self.explanation.section_id != self.section_id:
            msg = "Explanation section_id must match section_id."
            raise ValueError(msg)
        if self.source is SectionSource.PLUGIN and self.enriched_from_section_id is not None:
            msg = "Plugin sections cannot set enriched_from_section_id."
            raise ValueError(msg)
        if self.source is SectionSource.PROVIDER and self.enriched_from_section_id is None:
            msg = "Provider sections must set enriched_from_section_id."
            raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class AnalysisResult:
    """Aggregated plugin and optional provider analysis output."""

    sections: tuple[AnalysisSection, ...]
    trace: tuple[TraceEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.sections:
            msg = "AnalysisResult requires at least one section."
            raise ValueError(msg)
        if self.trace is None:
            object.__setattr__(self, "trace", ())
