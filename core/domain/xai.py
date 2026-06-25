"""XAI builders for analysis sections and explanations."""

from __future__ import annotations

from datetime import UTC, datetime

from core.domain.ids import ExplanationId, ProviderId, SectionId
from core.domain.models import (
    AnalysisExplanation,
    AnalysisSection,
    GeneratedBy,
    SectionSource,
    TraceEntry,
    TraceStep,
)
from core.metrics.context import get_correlation_id

_PLUGIN_CONFIDENCE = 0.75
_PROVIDER_CONFIDENCE = 0.65


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def build_plugin_explanation(
    *,
    section_id: SectionId,
    capability: str,
    plugin_id: str,
    content: str,
) -> AnalysisExplanation:
    """Build a plugin-generated explanation."""
    return AnalysisExplanation(
        explanation_id=ExplanationId.new(),
        section_id=section_id,
        confidence=_PLUGIN_CONFIDENCE,
        reasoning=(
            f"Plugin generated canonical analysis for capability: {capability}",
            f"Canonical result content: {content}",
        ),
        evidence=(
            f"plugin_id={plugin_id}",
            f"capability={capability}",
        ),
        generated_by=GeneratedBy.PLUGIN,
    )


def build_plugin_analysis_section(
    *,
    capability: str,
    title: str,
    content: str,
    plugin_id: str,
) -> AnalysisSection:
    """Build a plugin analysis section with explanation."""
    section_id = SectionId.new()
    explanation = build_plugin_explanation(
        section_id=section_id,
        capability=capability,
        plugin_id=plugin_id,
        content=content,
    )
    return AnalysisSection(
        section_id=section_id,
        capability=capability,
        title=title,
        content=content,
        source=SectionSource.PLUGIN,
        explanation=explanation,
    )


def build_provider_explanation(
    *,
    section_id: SectionId,
    plugin_section: AnalysisSection,
    provider_id: ProviderId,
    capability: str,
    content: str,
) -> AnalysisExplanation:
    """Build a provider-generated enrichment explanation."""
    return AnalysisExplanation(
        explanation_id=ExplanationId.new(),
        section_id=section_id,
        confidence=_PROVIDER_CONFIDENCE,
        reasoning=(
            f"Provider enriched plugin section: {plugin_section.section_id}",
            f"Enrichment explanation for capability: {capability}",
            f"Provider response: {content}",
        ),
        evidence=(
            f"enriched_from_section_id={plugin_section.section_id}",
            f"provider_id={provider_id}",
            f"plugin_content={plugin_section.content}",
        ),
        generated_by=GeneratedBy.PROVIDER,
    )


def build_provider_analysis_section(
    *,
    plugin_section: AnalysisSection,
    provider_id: ProviderId,
    capability: str,
    content: str,
) -> AnalysisSection:
    """Build a provider enrichment section linked to a plugin section."""
    section_id = SectionId.new()
    explanation = build_provider_explanation(
        section_id=section_id,
        plugin_section=plugin_section,
        provider_id=provider_id,
        capability=capability,
        content=content,
    )
    return AnalysisSection(
        section_id=section_id,
        capability=capability,
        title=f"Provider Enrichment ({provider_id})",
        content=content,
        source=SectionSource.PROVIDER,
        explanation=explanation,
        enriched_from_section_id=plugin_section.section_id,
    )


def build_plugin_trace_entry(capability: str) -> TraceEntry:
    return TraceEntry(
        step=TraceStep.PLUGIN,
        source=capability,
        timestamp=_utc_timestamp(),
        message="Plugin analysis completed",
        correlation_id=get_correlation_id(),
    )


def build_provider_trace_entry(provider_id: ProviderId) -> TraceEntry:
    return TraceEntry(
        step=TraceStep.PROVIDER,
        source=str(provider_id),
        timestamp=_utc_timestamp(),
        message="Provider enrichment completed",
        correlation_id=get_correlation_id(),
    )


def build_report_trace_entry(report_id: str) -> TraceEntry:
    return TraceEntry(
        step=TraceStep.REPORT,
        source=report_id,
        timestamp=_utc_timestamp(),
        message="Report aggregate synchronized",
        correlation_id=get_correlation_id(),
    )


def trace_entries_to_reason_steps(trace: tuple[TraceEntry, ...]) -> tuple[str, ...]:
    """Serialize trace entries for report explanation traces."""
    return tuple(
        f"{entry.step}:{entry.source}|{entry.timestamp}|{entry.message}"
        for entry in trace
    )
