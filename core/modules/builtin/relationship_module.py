"""Relationship engine builtin module."""

from __future__ import annotations

from core.modules.builtin.base import BuiltinModuleBase


class RelationshipModule(BuiltinModuleBase):
    """Stub module for relationship analysis."""

    def __init__(self) -> None:
        super().__init__(
            module_name="relationship",
            version="0.1.0",
            capabilities=("relationship.analysis",),
        )
