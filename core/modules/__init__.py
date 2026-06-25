"""Feature module system."""

from core.modules.interfaces import IModule
from core.modules.models import ModuleDescriptor
from core.modules.registry import ModuleRegistry, ModuleRegistryError

__all__ = [
    "IModule",
    "ModuleDescriptor",
    "ModuleRegistry",
    "ModuleRegistryError",
]
