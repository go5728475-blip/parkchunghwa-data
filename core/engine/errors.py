"""Engine error model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, kw_only=True)
class EngineError:
    """Structured engine error."""

    code: str
    message: str
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.details is None:
            object.__setattr__(self, "details", {})
