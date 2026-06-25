"""Provider enrichment helpers for analysis pipeline."""

from __future__ import annotations

from core.domain.ids import ProviderId
from core.domain.models import AnalysisSection
from core.domain.xai import build_provider_analysis_section

_ENRICHMENT_PROMPT = "Enrichment explanation for plugin analysis: {content}"


def enrich_with_provider(
    provider_manager: object,
    provider_id: ProviderId,
    plugin_section: AnalysisSection,
    capability: str,
) -> AnalysisSection:
    """Create a provider enrichment section from a plugin section."""
    prompt = _ENRICHMENT_PROMPT.format(content=plugin_section.content)
    context = {
        "capability": capability,
        "plugin_section_id": str(plugin_section.section_id),
        "plugin_title": plugin_section.title,
        "plugin_content": plugin_section.content,
        "plugin_source": plugin_section.source.value,
        "plugin_explanation_id": str(plugin_section.explanation.explanation_id),
    }
    enrichment_text = provider_manager.generate(provider_id, prompt, context)
    return build_provider_analysis_section(
        plugin_section=plugin_section,
        provider_id=provider_id,
        capability=capability,
        content=enrichment_text,
    )
