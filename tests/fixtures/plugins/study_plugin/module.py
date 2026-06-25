"""Dynamic study engine module."""

from __future__ import annotations

from sdk import BaseModule


class Module(BaseModule):
    """Study analysis module loaded from a directory package."""

    def __init__(self) -> None:
        super().__init__(
            name="study",
            version="0.2.0",
            author="MASTER ENGINE",
            description="Study analysis engine package",
            capabilities=("study.analysis",),
        )
