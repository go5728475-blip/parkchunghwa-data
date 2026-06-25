"""MASTER LOCK builtin module."""

from __future__ import annotations

from core.modules.builtin.base import BuiltinModuleBase


class MasterLockModule(BuiltinModuleBase):
    """Stub module for MASTER LOCK analysis."""

    def __init__(self) -> None:
        super().__init__(
            module_name="master_lock",
            version="0.1.0",
            capabilities=("master_lock.analysis",),
        )
