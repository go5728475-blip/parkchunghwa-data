"""Default runtime certification policy paths."""

from __future__ import annotations

import json
import os
from pathlib import Path


def get_default_certification_policy_path() -> Path:
    """Resolve the default declarative certification policy file path."""
    env_path = os.environ.get("MASTER_ENGINE_CERTIFICATION_POLICY")
    if env_path:
        return Path(env_path)
    return Path.cwd() / ".master_engine" / "certification_policy.json"


def ensure_default_certification_policy_file() -> Path:
    """Ensure the default certification policy JSON file exists."""
    policy_path = get_default_certification_policy_path()
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    if not policy_path.exists():
        policy_path.write_text(
            json.dumps(_DEFAULT_POLICY, indent=2) + "\n",
            encoding="utf-8",
        )
    return policy_path


_DEFAULT_POLICY = {
    "version": "1.0",
    "id": "runtime-default",
    "name": "Runtime Default Certification Policy",
    "rules": [
        {
            "id": "require-manifest",
            "severity": "fail",
            "actions": ["block_load"],
            "field": "manifest",
            "required": True,
        },
        {
            "id": "warn-provider",
            "severity": "warn",
            "actions": ["warn"],
            "field": "source",
            "forbidden": "openai",
        },
    ],
}
