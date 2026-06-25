"""CI runtime certification end-to-end suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.certification import main, run_check, run_runtime_status
from core.bootstrap.bootstrap import Bootstrap
from core.cli.main import load_module
from core.runtime.bootstrap import RuntimeBootstrap
from core.runtime.policy_cache import reset_default_policy_cache
from tests.fixtures.runtime_policy_helpers import write_runtime_policy


pytestmark = pytest.mark.ci


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
CERTIFIED = FIXTURES / "certified_plugin"


@pytest.fixture(autouse=True)
def _isolated_ci_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    reset_default_policy_cache()


def test_ci_runtime_boot_and_policy_load(tmp_path: Path) -> None:
    policy = write_runtime_policy(tmp_path)
    bootstrap = RuntimeBootstrap()

    runtime = bootstrap.boot(policy_path=policy)

    assert bootstrap.is_booted
    assert runtime.policy.id == "fixture-runtime-policy"


def test_ci_runtime_enforcement_and_registry(tmp_path: Path) -> None:
    policy = write_runtime_policy(tmp_path)
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy)
    bootstrap.enforce_plugin(
        "certified",
        {"manifest": {"name": "certified"}, "source": "sdk"},
    )

    bridge = bootstrap.registry_bridge()
    assert bridge.get_plugin_status("certified").runtime_status == "PASS"


def test_ci_runtime_audit_trail(tmp_path: Path) -> None:
    policy = write_runtime_policy(tmp_path)
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy)
    bootstrap.enforce_plugin("certified", {"manifest": {"name": "certified"}, "source": "sdk"})

    assert len(bootstrap.registry.get_audit_history()) >= 2


def test_ci_load_module_certified_only(tmp_path: Path) -> None:
    write_runtime_policy(tmp_path)
    bootstrap = Bootstrap().build()

    exit_code = load_module(
        str(CERTIFIED),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
    )

    assert exit_code == 0
    assert bootstrap.module_registry().exists("certified")


def test_ci_runtime_reload(tmp_path: Path) -> None:
    policy = write_runtime_policy(tmp_path)
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy)
    bootstrap.reload_policy(policy)

    assert bootstrap.runtime.policy is not None


def test_ci_cli_runtime_check(tmp_path: Path) -> None:
    policy = write_runtime_policy(tmp_path)

    exit_code = run_check(
        str(policy),
        use_runtime=True,
        plugin_id="certified",
        target={"manifest": {"name": "certified"}, "source": "sdk"},
    )

    assert exit_code == 0


def test_ci_cli_runtime_status(tmp_path: Path) -> None:
    write_runtime_policy(tmp_path)

    exit_code = main(["runtime-status", "--format", "json"])

    assert exit_code == 0
