"""End-to-end runtime load pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.bootstrap.bootstrap import Bootstrap
from core.cli.main import load_module
from core.runtime.bootstrap import RuntimeBootstrap
from core.runtime.load_pipeline import RuntimeLoadError, enforce_runtime_before_load
from core.runtime.policy_cache import reset_default_policy_cache
from tests.fixtures.runtime_policy_helpers import RUNTIME_POLICY, write_runtime_policy


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
CERTIFIED = FIXTURES / "certified_plugin"
WARNING = FIXTURES / "warning_plugin"
FAILED = FIXTURES / "failed_plugin"
POLICY = FIXTURES / "policy_plugin"
NO_POLICY = FIXTURES / "no_policy_plugin"


@pytest.fixture(autouse=True)
def _isolated_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    reset_default_policy_cache()


@pytest.fixture
def policy_path(tmp_path: Path) -> Path:
    return write_runtime_policy(tmp_path)


def test_runtime_pipeline_pass(policy_path: Path) -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)

    decision, _, plugin, loader = enforce_runtime_before_load(
        str(CERTIFIED),
        runtime_bootstrap=bootstrap,
        certified_only=True,
    )
    loader.unload(plugin.name())

    assert decision.decision.status.value == "PASS"
    assert decision.registered is True


def test_runtime_pipeline_warn_blocked_in_certified_only(policy_path: Path) -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)

    with pytest.raises(RuntimeLoadError, match="certified-only"):
        enforce_runtime_before_load(
            str(WARNING),
            runtime_bootstrap=bootstrap,
            certified_only=True,
        )


def test_runtime_pipeline_certification_fail(policy_path: Path) -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)

    with pytest.raises(Exception, match="certification failed|Incompatible"):
        enforce_runtime_before_load(
            str(FAILED),
            runtime_bootstrap=bootstrap,
            certified_only=True,
        )


def test_manifest_policy_auto_load() -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(plugin_path=POLICY)

    assert bootstrap.runtime.policy.id == "fixture-runtime-policy"


def test_load_module_certified_only_with_runtime(policy_path: Path, capsys) -> None:
    bootstrap = Bootstrap().build()

    exit_code = load_module(
        str(CERTIFIED),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Runtime Status:        PASS" in captured.out
    assert bootstrap.module_registry().exists("certified")


def test_registry_lookup_after_load(policy_path: Path) -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)
    enforce_runtime_before_load(
        str(CERTIFIED),
        runtime_bootstrap=bootstrap,
        certified_only=True,
    )

    bridge = bootstrap.registry_bridge()
    status = bridge.get_plugin_status("certified")

    assert status.runtime_status == "PASS"


def test_audit_trail_after_enforcement(policy_path: Path) -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)
    enforce_runtime_before_load(
        str(NO_POLICY),
        runtime_bootstrap=bootstrap,
        certified_only=True,
    )

    history = bootstrap.registry.get_audit_history()
    events = {entry.event for entry in history}

    assert "POLICY_ENFORCED" in events or "POLICY_FAILED" in events
