"""End-to-end runtime reload tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.runtime.bootstrap import RuntimeBootstrap
from core.runtime.policy_cache import reset_default_policy_cache
from tests.fixtures.runtime_policy_helpers import write_runtime_policy


@pytest.fixture(autouse=True)
def _isolated_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    reset_default_policy_cache()


def test_e2e_reload_module_metadata(tmp_path: Path) -> None:
    policy_path = write_runtime_policy(tmp_path)
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)
    bootstrap.enforce_plugin(
        "health",
        {"manifest": {"name": "health"}, "source": "sdk"},
    )

    bootstrap.reload_policy(policy_path)

    assert bootstrap.runtime.policy.id == "fixture-runtime-policy"
    assert bootstrap.registry.list_runtime_plugins() == ("health",)
