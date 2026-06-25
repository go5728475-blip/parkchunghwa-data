"""Map certification results to compatibility levels."""

from __future__ import annotations

from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.certification.result import PluginCertificationResult


def map_result_to_compatibility_level(
    result: PluginCertificationResult | None,
) -> PluginCompatibilityLevel:
    """Derive compatibility level from a certification result."""
    if result is None:
        return PluginCompatibilityLevel.UNKNOWN
    if not result.passed:
        return PluginCompatibilityLevel.INCOMPATIBLE
    if result.warnings:
        return PluginCompatibilityLevel.PARTIAL
    return PluginCompatibilityLevel.COMPATIBLE
