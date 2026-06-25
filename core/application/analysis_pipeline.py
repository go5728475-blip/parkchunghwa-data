"""Analysis pipeline orchestrating plugin and provider enrichment."""

from __future__ import annotations

from typing import Any

from core.application.provider_enrichment import enrich_with_provider
from core.domain.ids import ProviderId
from core.domain.models import AnalysisResult, TraceEntry
from core.domain.xai import build_plugin_trace_entry, build_provider_trace_entry


class AnalysisPipeline:
    """Runs plugin analysis, XAI metadata, and optional provider enrichment."""

    def __init__(
        self,
        plugin_manager: object,
        provider_manager: object | None = None,
    ) -> None:
        self._plugin_manager = plugin_manager
        self._provider_manager = provider_manager

    def run(
        self,
        *,
        capability: str,
        input_data: dict[str, Any],
        provider_id: ProviderId | None = None,
    ) -> AnalysisResult:
        """Execute plugin analysis and optional provider enrichment."""
        plugin_section = self._plugin_manager.execute_analysis_section(
            capability,
            input_data,
        )
        sections = [plugin_section]
        trace: list[TraceEntry] = [build_plugin_trace_entry(capability)]

        if provider_id is not None:
            if self._provider_manager is None:
                msg = "Provider manager is not configured."
                raise RuntimeError(msg)
            provider_section = enrich_with_provider(
                self._provider_manager,
                provider_id,
                plugin_section,
                capability,
            )
            sections.append(provider_section)
            trace.append(build_provider_trace_entry(provider_id))

        return AnalysisResult(sections=tuple(sections), trace=tuple(trace))
