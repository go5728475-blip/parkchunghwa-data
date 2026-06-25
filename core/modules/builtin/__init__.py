"""Builtin engine modules."""

from __future__ import annotations

from core.modules.builtin.career_module import CareerModule
from core.modules.builtin.master_lock_module import MasterLockModule
from core.modules.builtin.relationship_module import RelationshipModule
from core.modules.builtin.wealth_module import WealthModule
from core.modules.interfaces import IModule


def create_builtin_modules() -> tuple[IModule, ...]:
    """Create the default builtin engine modules."""
    return (
        MasterLockModule(),
        WealthModule(),
        CareerModule(),
        RelationshipModule(),
    )
