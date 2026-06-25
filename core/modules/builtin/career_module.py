"""Career engine builtin module."""

from __future__ import annotations

from core.modules.builtin.base import BuiltinModuleBase


class CareerModule(BuiltinModuleBase):
    """Stub module for career analysis."""

    def __init__(self) -> None:
        super().__init__(
            module_name="career",
            version="0.1.0",
            capabilities=("career.analysis",),
        )
