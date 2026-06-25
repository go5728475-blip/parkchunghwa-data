"""Plugin compatibility levels."""

from __future__ import annotations

from enum import StrEnum


class PluginCompatibilityLevel(StrEnum):
    """Compatibility classification for certified plugins."""

    UNKNOWN = "UNKNOWN"
    COMPATIBLE = "COMPATIBLE"
    PARTIAL = "PARTIAL"
    INCOMPATIBLE = "INCOMPATIBLE"
