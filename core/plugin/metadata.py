"""Plugin metadata model."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.domain.ids import PluginId


@dataclass(frozen=True, kw_only=True)
class PluginMetadata:
    """Immutable descriptor for a registered plugin."""

    plugin_id: PluginId
    name: str
    version: str
    description: str
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Plugin name cannot be empty.")
        if self.capabilities is None:
            object.__setattr__(self, "capabilities", ())
        if self.dependencies is None:
            object.__setattr__(self, "dependencies", ())
