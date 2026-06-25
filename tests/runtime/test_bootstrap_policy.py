"""Tests for runtime bootstrap policy integration."""

from __future__ import annotations

import json
from pathlib import Path

from core.runtime.bootstrap import RuntimeBootstrap


def _write_policy(directory: Path, policy_id: str = "custom-policy") -> Path:
    path = directory / "custom_policy.json"
    path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "id": policy_id,
                "name": "Custom Policy",
                "rules": [
                    {
                        "id": "require-manifest",
                        "severity": "fail",
                        "actions": ["block_load"],
                        "field": "manifest",
                        "required": True,
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    return path


def test_bootstrap_default_policy(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    bootstrap = RuntimeBootstrap()

    runtime = bootstrap.boot()

    assert bootstrap.is_booted is True
    assert runtime.policy is not None
    assert runtime.policy.id == "runtime-default"


def test_bootstrap_custom_policy(tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path)
    bootstrap = RuntimeBootstrap()

    runtime = bootstrap.boot(policy_path=policy_path)

    assert runtime.policy.id == "custom-policy"


def test_bootstrap_manifest_policy(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "sample_plugin"
    plugin_dir.mkdir()
    policy_path = _write_policy(plugin_dir, "manifest-policy")
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "sample",
                "version": "1.0.0",
                "author": "test",
                "description": "test",
                "capabilities": ["sample.analysis"],
                "module_class": "Module",
                "certification": {"policy": policy_path.name},
            },
        ),
        encoding="utf-8",
    )
    bootstrap = RuntimeBootstrap()

    runtime = bootstrap.boot(plugin_path=plugin_dir)

    assert runtime.policy.id == "manifest-policy"


def test_bootstrap_parse_policy_option() -> None:
    policy_path, remaining = RuntimeBootstrap.parse_policy_option(
        ["--policy", "policy.yaml", "check"],
    )

    assert policy_path == "policy.yaml"
    assert remaining == ["check"]
