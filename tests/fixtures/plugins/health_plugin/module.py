"""Dynamic health engine module."""

from __future__ import annotations

from sdk import BaseModule


class Module(BaseModule):
    """Health analysis module loaded from a directory package."""

    def __init__(self) -> None:
        super().__init__(
            name="health",
            version="1.0.0",
            author="MASTER ENGINE",
            description="Health analysis engine package",
            capabilities=("health.analysis",),
        )
