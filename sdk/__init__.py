"""MASTER ENGINE Plugin SDK."""

from sdk.manifest import PluginManifest, load_manifest
from sdk.module import BaseModule, IModule
from sdk.plugin import BaseCapabilityPlugin, BasePlugin, IPlugin, PluginMetadata
from sdk.templates import create_plugin_template
from sdk.validation import ValidationError, validate_manifest, validate_plugin_package
from sdk.version import PLUGIN_SDK_VERSION

__all__ = [
    "PLUGIN_SDK_VERSION",
    "BaseCapabilityPlugin",
    "BaseModule",
    "BasePlugin",
    "IModule",
    "IPlugin",
    "PluginManifest",
    "PluginMetadata",
    "ValidationError",
    "create_plugin_template",
    "load_manifest",
    "validate_manifest",
    "validate_plugin_package",
]
