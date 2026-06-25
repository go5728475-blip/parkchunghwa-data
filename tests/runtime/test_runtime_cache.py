"""Tests for runtime policy cache."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.runtime.certification_runtime import CertificationRuntime
from core.runtime.policy_cache import RuntimePolicyCache, reset_default_policy_cache


POLICY = {
    "version": "1.0",
    "id": "cache-policy",
    "name": "Cache Policy",
    "rules": [
        {
            "id": "require-manifest",
            "severity": "fail",
            "actions": ["block_load"],
            "field": "manifest",
            "required": True,
        },
    ],
}


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    reset_default_policy_cache()


def test_cache_hit_on_second_load(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(POLICY), encoding="utf-8")
    cache = RuntimePolicyCache()
    runtime = CertificationRuntime(policy_cache=cache)

    runtime.load_policy(policy_path)
    runtime.load_policy(policy_path)

    events = [entry.event for entry in runtime.registry.get_audit_history()]
    assert "POLICY_CACHE_HIT" in events


def test_cache_miss_on_first_load(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(POLICY), encoding="utf-8")
    cache = RuntimePolicyCache()
    runtime = CertificationRuntime(policy_cache=cache)

    runtime.load_policy(policy_path)

    events = [entry.event for entry in runtime.registry.get_audit_history()]
    assert "POLICY_CACHE_MISS" in events


def test_cache_invalidate(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(POLICY), encoding="utf-8")
    cache = RuntimePolicyCache()
    runtime = CertificationRuntime(policy_cache=cache)
    runtime.load_policy(policy_path)

    runtime.invalidate_policy_cache(policy_path)

    assert cache.get(policy_path) is None


def test_cache_reload(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(POLICY), encoding="utf-8")
    cache = RuntimePolicyCache()
    runtime = CertificationRuntime(policy_cache=cache)
    runtime.initialize(policy_path)

    updated = dict(POLICY)
    updated["name"] = "Updated Cache Policy"
    policy_path.write_text(json.dumps(updated), encoding="utf-8")

    reloaded = runtime.reload_policy(policy_path)

    assert reloaded.name == "Updated Cache Policy"


def test_cache_clear(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(POLICY), encoding="utf-8")
    cache = RuntimePolicyCache()
    runtime = CertificationRuntime(policy_cache=cache)
    runtime.load_policy(policy_path)

    runtime.clear_policy_cache()

    assert cache.paths() == ()
