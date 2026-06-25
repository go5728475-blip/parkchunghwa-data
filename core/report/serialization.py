"""Shared serialization helpers for report export."""

from __future__ import annotations

from typing import Any

from core.domain.built_report import BuiltReport, CapabilityReportGroup, ReportTocEntry
from core.domain.models import TraceEntry
from core.domain.value_objects import ReportSection


def report_section_to_dict(section: ReportSection) -> dict[str, Any]:
    """Convert a report section to a JSON-serializable dict."""
    return {
        "title": section.title,
        "content": section.content,
        "section_id": section.section_id,
        "explanation": {
            "explanation_id": section.explanation_id,
            "generated_by": section.generated_by,
            "confidence": section.confidence.value,
            "reasoning": list(section.reasoning),
            "evidence": list(section.evidence),
            "enriched_from_section_id": section.enriched_from_section_id,
        },
    }


def toc_entry_to_dict(entry: ReportTocEntry) -> dict[str, Any]:
    """Convert a TOC entry to a JSON-serializable dict."""
    return {
        "order": entry.order,
        "title": entry.title,
        "capability": entry.capability,
    }


def capability_group_to_dict(group: CapabilityReportGroup) -> dict[str, Any]:
    """Convert a capability group to a JSON-serializable dict."""
    return {
        "capability": group.capability,
        "label": group.label,
        "sections": [report_section_to_dict(section) for section in group.sections],
    }


def trace_entry_to_dict(entry: TraceEntry) -> dict[str, Any]:
    """Convert a trace entry to a JSON-serializable dict."""
    return {
        "step": entry.step.value,
        "source": entry.source,
        "timestamp": entry.timestamp,
        "message": entry.message,
        "event_id": entry.event_id,
        "event_type": entry.event_type,
    }


def built_report_to_dict(report: BuiltReport) -> dict[str, Any]:
    """Convert a built report to a JSON-serializable dict without information loss."""
    return {
        "report_id": str(report.report_id),
        "title": report.title,
        "summary": report.summary,
        "generated_at": report.generated_at,
        "toc": [toc_entry_to_dict(entry) for entry in report.toc],
        "capability_groups": [
            capability_group_to_dict(group) for group in report.capability_groups
        ],
        "sections": [report_section_to_dict(section) for section in report.sections],
        "trace": [trace_entry_to_dict(entry) for entry in report.trace],
    }
