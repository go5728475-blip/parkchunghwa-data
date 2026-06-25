"""Runtime certification load pipeline wiring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.certification.models import DecisionStatus
from core.plugins.certification.loading import CertificationLoadError, load_plugin_for_certification
from core.runtime.bootstrap import RuntimeBootstrap
from core.runtime.certification_runtime import CertificationRuntime, RuntimeDecision


class RuntimeLoadError(Exception):
    """Raised when runtime policy blocks plugin loading."""


def build_enforcement_target(plugin: object, plugin_path: str) -> dict[str, Any]:
    manifest = getattr(plugin, "manifest", None)
    manifest_payload: dict[str, Any] | None = None
    if manifest is not None:
        manifest_payload = {
            "name": getattr(manifest, "name", None),
            "version": getattr(manifest, "version", None),
        }
    source = _read_module_source(plugin_path)
    return {
        "manifest": manifest_payload,
        "source": source,
    }


def enforce_runtime_before_load(
    path: str,
    *,
    runtime_bootstrap: RuntimeBootstrap | None = None,
    policy_path: str | Path | None = None,
    certified_only: bool = False,
    certification_gate: object | None = None,
    certified_registry: object | None = None,
    require_registered: bool = False,
    container: object | None = None,
) -> tuple[RuntimeDecision, object | None, object, object]:
    """Run certification gate and runtime enforcement before module load."""
    from core.plugins.certification.load_gate import certify_plugin_before_load

    plugin, certification_loader = load_plugin_for_certification(path)
    certification_record = None

    if certified_only:
        certification_record = certify_plugin_before_load(
            plugin,
            certification_gate,
            require_registered=require_registered,
            registry=certified_registry if require_registered else None,
            container=container,
        )

    bootstrap = runtime_bootstrap or RuntimeBootstrap()
    if not bootstrap.is_booted:
        bootstrap.boot(policy_path=policy_path, plugin_path=path)
    target = build_enforcement_target(plugin, path)
    plugin_id = str(getattr(getattr(plugin, "manifest", None), "name", plugin.name()))
    runtime_decision = bootstrap.enforce_plugin(plugin_id, target)

    if runtime_decision.decision.status is DecisionStatus.FAIL:
        raise RuntimeLoadError(
            f"Runtime policy blocked plugin {plugin_id}: "
            f"{', '.join(runtime_decision.decision.violations)}",
        )
    if certified_only and runtime_decision.decision.status is DecisionStatus.WARN:
        raise RuntimeLoadError(
            f"Runtime policy warning blocked in certified-only mode for {plugin_id}: "
            f"{', '.join(runtime_decision.decision.recommendations)}",
        )

    return runtime_decision, certification_record, plugin, certification_loader


def resolve_manifest_policy_path(plugin_path: str | Path) -> Path | None:
    return CertificationRuntime.resolve_manifest_policy_path(plugin_path)


def _read_module_source(plugin_path: str) -> str:
    module_path = Path(plugin_path) / "module.py"
    if module_path.exists():
        return module_path.read_text(encoding="utf-8")
    return ""


def reevaluate_plugin_metadata(
    runtime: CertificationRuntime,
    plugin_id: str,
    target: dict[str, Any],
) -> RuntimeDecision:
    """Re-evaluate plugin metadata without unloading the module."""
    return runtime.enforce_plugin_load(plugin_id, target)
