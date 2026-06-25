"""Module metadata models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ModuleDescriptor:
    """Describes a registered engine module."""

    name: str
    version: str
    capabilities: tuple[str, ...]
    loaded: bool = False
