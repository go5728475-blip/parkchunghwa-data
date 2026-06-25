"""Tests for runtime status CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.certification import main, run_runtime_status
from core.certification.models import CertificationDecision, DecisionStatus
from core.runtime.bootstrap import RuntimeBootstrap
from core.runtime.policy_cache import reset_default_policy_cache
from tests.fixtures.runtime_policy_helpers import write_runtime_policy


@pytest.fixture(autouse=True)
def _isolated_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    reset_default_policy_cache()


def test_runtime_status_table_output(tmp_path: Path) -> None:
    policy = write_runtime_policy(tmp_path)
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy)
    bootstrap.registry.set_decision("health", CertificationDecision(status=DecisionStatus.PASS))

    exit_code = run_runtime_status(bootstrap=bootstrap)
    assert exit_code == 0


def test_runtime_status_json_output(tmp_path: Path, capsys) -> None:
    policy = write_runtime_policy(tmp_path)
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy)

    exit_code = run_runtime_status(bootstrap=bootstrap, output_format="json")
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out[captured.out.index("{") :])
    assert payload["loaded_policy"] == "fixture-runtime-policy"


def test_runtime_status_verbose(capsys, tmp_path: Path) -> None:
    policy = write_runtime_policy(tmp_path)
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy)
    bootstrap.enforce_plugin("health", {"manifest": {"name": "health"}, "source": "sdk"})

    run_runtime_status(bootstrap=bootstrap, verbose=True)
    captured = capsys.readouterr()

    assert "runtime_plugins" in captured.out or "health" in captured.out


def test_runtime_status_reload(tmp_path: Path) -> None:
    policy = write_runtime_policy(tmp_path)
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy)

    exit_code = run_runtime_status(bootstrap=bootstrap, reload=True)

    assert exit_code == 0


def test_main_runtime_status_command(tmp_path: Path, capsys) -> None:
    write_runtime_policy(tmp_path)

    exit_code = main(["runtime-status", "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Runtime Certification Status" in captured.out
