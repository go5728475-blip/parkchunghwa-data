"""Wealth engine builtin module."""

from __future__ import annotations

from core.modules.builtin.base import BuiltinModuleBase


class WealthModule(BuiltinModuleBase):
    """Stub module for wealth analysis."""

    def __init__(self) -> None:
        super().__init__(
            module_name="wealth",
            version="0.1.0",
            capabilities=("wealth.analysis",),
        )
