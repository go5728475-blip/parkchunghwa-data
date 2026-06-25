"""Bootstrap configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class EngineConfiguration:
    """Immutable engine configuration for composition root wiring."""

    environment: str = "development"
    debug: bool = False
    supported_capabilities: tuple[str, ...] | None = None
    event_storage: str = "inmemory"
    sqlite_path: str = "master_engine.db"

    def __post_init__(self) -> None:
        if self.event_storage not in {"inmemory", "sqlite"}:
            msg = "event_storage must be 'inmemory' or 'sqlite'."
            raise ValueError(msg)
        if not self.sqlite_path.strip():
            msg = "sqlite_path cannot be empty."
            raise ValueError(msg)

    @classmethod
    def default(cls) -> EngineConfiguration:
        """Return the default development configuration."""
        return cls()
