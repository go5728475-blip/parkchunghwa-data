"""Tests for runtime policy reload."""

from __future__ import annotations

import json
from pathlib import Path

from core.certification.models import DecisionStatus
from core.runtime.bootstrap import RuntimeBootstrap


def _policy(path: Path, policy_id: str, *, forbid: str | None = None) -> None:
    rules = [
        {
            "id": "require-manifest",
            "severity": "fail",
            "actions": ["block_load"],
            "field": "manifest",
            "required": True,
        },
    ]
    if forbid:
        rules.append(
            {
                "id": "warn-provider",
                "severity": "warn",
                "actions": ["warn"],
                "field": "source",
                "forbidden": forbid,
            },
        )
    path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "id": policy_id,
                "name": policy_id,
                "rules": rules,
            },
        ),
        encoding="utf-8",
    )


def test_reload_policy_updates_registry(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    _policy(policy_path, "initial-policy", forbid="openai")
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)
    bootstrap.enforce_plugin(
        "health",
        {"manifest": {"name": "health"}, "source": "openai integration"},
    )
    assert bootstrap.registry.get_decision("health").status is DecisionStatus.WARN

    _policy(policy_path, "strict-policy", forbid="openai")
    bootstrap.reload_policy(policy_path)

    assert bootstrap.runtime.policy.id == "strict-policy"
    assert bootstrap.registry.get_policy().id == "strict-policy"


def test_reload_reevaluates_metadata_without_unload(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    _policy(policy_path, "reload-policy", forbid="openai")
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)
    bootstrap.enforce_plugin(
        "health",
        {"manifest": {"name": "health"}, "source": "sdk"},
    )

    bootstrap.reload_policy(policy_path)

    assert bootstrap.registry.list_runtime_plugins() == ("health",)
