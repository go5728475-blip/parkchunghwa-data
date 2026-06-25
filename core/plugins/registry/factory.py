"""Certified plugin registry factory helpers."""

from __future__ import annotations

from pathlib import Path

from core.plugins.registry.certified import CertifiedPluginRegistry
from core.plugins.registry.json_store import JsonCertifiedPluginRegistryStore


def create_in_memory_certified_plugin_registry() -> CertifiedPluginRegistry:
    """Create an in-memory certified plugin registry."""
    return CertifiedPluginRegistry()


def create_json_certified_plugin_registry(path: str | Path) -> CertifiedPluginRegistry:
    """Create a certified plugin registry backed by a JSON file."""
    store = JsonCertifiedPluginRegistryStore(path)
    return CertifiedPluginRegistry(store=store)
