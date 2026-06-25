"""Default paths for certified plugin registry."""

from __future__ import annotations

import json
import os
from pathlib import Path


def get_default_certified_registry_path() -> Path:
    """Resolve the default certified plugin registry file path."""
    env_path = os.environ.get("MASTER_ENGINE_CERTIFIED_REGISTRY")
    if env_path:
        return Path(env_path)
    return Path.cwd() / ".master_engine" / "certified_plugins.json"


def ensure_default_registry_directory() -> Path:
    """Ensure the default certified plugin registry directory exists."""
    registry_path = get_default_certified_registry_path()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    return registry_path.parent


def ensure_default_registry_file() -> Path:
    """Ensure the default certified plugin registry JSON file exists."""
    ensure_default_registry_directory()
    registry_path = get_default_certified_registry_path()
    if not registry_path.exists():
        registry_path.write_text(
            json.dumps({"plugins": {}}, indent=2) + "\n",
            encoding="utf-8",
        )
    return registry_path


def get_default_audit_log_path() -> Path:
    """Resolve the default registry audit log file path."""
    env_path = os.environ.get("MASTER_ENGINE_AUDIT_LOG")
    if env_path:
        return Path(env_path)
    return Path.cwd() / ".master_engine" / "registry_audit.json"


def ensure_default_audit_file() -> Path:
    """Ensure the default registry audit log JSON file exists."""
    ensure_default_registry_directory()
    audit_path = get_default_audit_log_path()
    if not audit_path.exists():
        audit_path.write_text(
            json.dumps({"entries": []}, indent=2) + "\n",
            encoding="utf-8",
        )
    return audit_path
