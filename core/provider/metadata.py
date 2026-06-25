"""Provider metadata model."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.domain.ids import ProviderId


@dataclass(frozen=True, kw_only=True)
class ProviderMetadata:
    """Immutable descriptor for a registered provider."""

    provider_id: ProviderId
    name: str
    version: str
    model: str
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Provider name cannot be empty.")
        if not self.model.strip():
            raise ValueError("Provider model cannot be empty.")
        if self.capabilities is None:
            object.__setattr__(self, "capabilities", ())
