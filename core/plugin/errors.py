"""Plugin error types."""

from __future__ import annotations


class PluginError(Exception):
    """Base plugin error."""


class PluginNotFoundError(PluginError):
    """Raised when a plugin cannot be found."""


class DuplicatePluginError(PluginError):
    """Raised when registering the same plugin twice."""


class PluginExecutionError(PluginError):
    """Raised when plugin execution fails or is not allowed."""
