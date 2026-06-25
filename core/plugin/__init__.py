"""Plugin foundation exports."""

from core.plugin.analysis_stubs import (
    CareerStubPlugin,
    MasterLockStubPlugin,
    RelationshipStubPlugin,
    WealthStubPlugin,
)
from core.plugin.errors import (
    DuplicatePluginError,
    PluginError,
    PluginExecutionError,
    PluginNotFoundError,
)
from core.plugin.interface import PluginInterface
from core.plugin.loader import PluginLoader
from core.plugin.manager import PluginManager
from core.plugin.metadata import PluginMetadata
from core.plugin.registry import PluginRegistry
from core.plugin.stub import StubPlugin

from core.plugin.stub import StubPlugin

__all__ = [
    "CareerStubPlugin",
    "DuplicatePluginError",
    "MasterLockStubPlugin",
    "PluginError",
    "PluginExecutionError",
    "PluginInterface",
    "PluginLoader",
    "PluginManager",
    "PluginMetadata",
    "PluginNotFoundError",
    "PluginRegistry",
    "RelationshipStubPlugin",
    "StubPlugin",
    "WealthStubPlugin",
]
