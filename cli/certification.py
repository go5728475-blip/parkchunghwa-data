"""Certification policy CLI commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from core.certification.errors import PolicyLoadError, PolicyValidationError
from core.certification.models import CertificationDecision, DecisionStatus
from core.certification.policy_enforcer import CertificationPolicyEnforcer
from core.certification.policy_loader import CertificationPolicyLoader
from core.certification.policy_validator import CertificationPolicyValidator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="master certification")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a policy file")
    validate_parser.add_argument("policy_path", help="Path to policy YAML or JSON file")
    validate_parser.add_argument(
        "--format",
        choices=("json", "table"),
        default="table",
    )

    check_parser = subparsers.add_parser("check", help="Enforce a policy against a target")
    check_parser.add_argument("policy_path", nargs="?", default=None)
    check_parser.add_argument(
        "--format",
        choices=("json", "table"),
        default="table",
    )
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARN as failure",
    )
    check_parser.add_argument(
        "--target",
        help="JSON file containing enforcement target",
    )
    check_parser.add_argument(
        "--runtime",
        action="store_true",
        help="Use runtime bootstrap registry for enforcement",
    )
    check_parser.add_argument(
        "--plugin",
        help="Plugin id for runtime enforcement",
    )
    check_parser.add_argument(
        "--history",
        action="store_true",
        help="Print runtime audit history after check",
    )
    status_parser = subparsers.add_parser(
        "runtime-status",
        help="Show runtime certification status",
    )
    status_parser.add_argument(
        "--format",
        choices=("json", "table"),
        default="table",
    )
    status_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include detailed plugin status",
    )
    status_parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload runtime policy before showing status",
    )
    status_parser.add_argument(
        "--policy",
        help="Optional policy path for bootstrap",
    )
    return parser


def run_validate(
    policy_path: str,
    *,
    output_format: str = "table",
) -> int:
    loader = CertificationPolicyLoader()
    validator = CertificationPolicyValidator()
    try:
        policy = loader.load(policy_path)
        validator.validate(policy)
    except (PolicyLoadError, PolicyValidationError) as exc:
        print(f"[MASTER ENGINE] Policy validation failed: {exc}")
        return 2
    payload = {
        "status": "PASS",
        "policy_id": policy.id,
        "policy_name": policy.name,
        "version": policy.version,
        "rules": len(policy.rules),
    }
    _print_result(payload, output_format=output_format, title="Policy Validated")
    return 0


def run_check(
    policy_path: str | None = None,
    *,
    output_format: str = "table",
    strict: bool = False,
    target_path: str | None = None,
    target: dict[str, Any] | None = None,
    use_runtime: bool = False,
    plugin_id: str | None = None,
    show_history: bool = False,
    bootstrap: object | None = None,
) -> int:
    if use_runtime:
        return _run_runtime_check(
            policy_path,
            output_format=output_format,
            strict=strict,
            target_path=target_path,
            target=target,
            plugin_id=plugin_id,
            show_history=show_history,
            bootstrap=bootstrap,
        )
    resolved_path = policy_path or _default_policy_path()
    loader = CertificationPolicyLoader()
    validator = CertificationPolicyValidator()
    enforcer = CertificationPolicyEnforcer()
    try:
        policy = loader.load(resolved_path)
        validator.validate(policy)
    except (PolicyLoadError, PolicyValidationError) as exc:
        print(f"[MASTER ENGINE] Policy check failed: {exc}")
        return 2
    enforcement_target = target or _load_target(target_path)
    decision = enforcer.enforce(policy, enforcement_target, {})
    exit_code = decision_to_exit_code(decision, strict=strict)
    payload = decision_to_payload(decision, policy_id=policy.id)
    _print_result(payload, output_format=output_format, title="Policy Check")
    return exit_code


def _run_runtime_check(
    policy_path: str | None,
    *,
    output_format: str,
    strict: bool,
    target_path: str | None,
    target: dict[str, Any] | None,
    plugin_id: str | None,
    show_history: bool,
    bootstrap: object | None,
) -> int:
    from core.runtime.bootstrap import RuntimeBootstrap

    runtime_bootstrap = bootstrap or RuntimeBootstrap()
    try:
        runtime_bootstrap.boot(policy_path=policy_path)
    except (PolicyLoadError, PolicyValidationError) as exc:
        print(f"[MASTER ENGINE] Runtime policy check failed: {exc}")
        return 2
    enforcement_target = target or _load_target(target_path)
    resolved_plugin_id = plugin_id or str(
        enforcement_target.get("manifest", {}).get("name", "unknown"),
    )
    runtime_decision = runtime_bootstrap.enforce_plugin(
        resolved_plugin_id,
        enforcement_target,
    )
    exit_code = decision_to_exit_code(runtime_decision.decision, strict=strict)
    payload = decision_to_payload(
        runtime_decision.decision,
        policy_id=runtime_bootstrap.runtime.policy.id,  # type: ignore[union-attr]
    )
    payload["registered"] = runtime_decision.registered
    payload["plugin_id"] = resolved_plugin_id
    _print_result(payload, output_format=output_format, title="Runtime Policy Check")
    if show_history:
        _print_audit_history(runtime_bootstrap.registry.get_audit_history(), output_format)
    return exit_code


def _print_audit_history(history: tuple[object, ...], output_format: str) -> None:
    print("[MASTER ENGINE] Runtime Audit History")
    if not history:
        print("  (none)")
        return
    if output_format == "json":
        print(
            json.dumps(
                [
                    {
                        "timestamp": entry.timestamp,
                        "event": entry.event,
                        "plugin_id": entry.plugin_id,
                        "policy_id": entry.policy_id,
                        "decision": entry.decision,
                        "violations": list(entry.violations),
                    }
                    for entry in history
                ],
                indent=2,
            ),
        )
        return
    for entry in history:
        print(f"  {entry.timestamp} | {entry.event} | plugin={entry.plugin_id}")


def run_runtime_status(
    *,
    output_format: str = "table",
    verbose: bool = False,
    reload: bool = False,
    policy_path: str | None = None,
    bootstrap: object | None = None,
    certified_registry: object | None = None,
) -> int:
    from core.runtime.bootstrap import RuntimeBootstrap

    runtime_bootstrap = bootstrap or RuntimeBootstrap()
    if not runtime_bootstrap.is_booted:
        runtime_bootstrap.boot(policy_path=policy_path)
    if reload:
        runtime_bootstrap.reload_policy(policy_path)

    bridge = runtime_bootstrap.registry_bridge(certified_registry)
    summary = bridge.certification_summary()
    policy = runtime_bootstrap.runtime.policy
    cache_paths = runtime_bootstrap.runtime.policy_cache.paths()

    payload: dict[str, object] = {
        "loaded_policy": policy.id if policy else None,
        "policy_version": policy.version if policy else None,
        "runtime_cache": list(cache_paths),
        "certified_plugins": list(summary["certified_plugins"]),
        "warning_plugins": list(summary["warning_plugins"]),
        "blocked_plugins": list(summary["blocked_plugins"]),
        "audit_count": summary["audit_count"],
    }
    if verbose:
        payload["runtime_plugins"] = [
            {
                "plugin_id": plugin_id,
                "status": bridge.get_plugin_status(plugin_id).runtime_status,
                "certified": bridge.get_plugin_status(plugin_id).certified,
            }
            for plugin_id in summary["runtime_plugins"]
        ]
    _print_result(payload, output_format=output_format, title="Runtime Certification Status")
    return 0


def decision_to_exit_code(decision: CertificationDecision, *, strict: bool = False) -> int:
    if decision.status is DecisionStatus.FAIL:
        return 2
    if decision.status is DecisionStatus.WARN:
        return 1 if not strict else 1
    return 0


def decision_to_payload(
    decision: CertificationDecision,
    *,
    policy_id: str,
) -> dict[str, object]:
    return {
        "status": decision.status.value,
        "policy_id": policy_id,
        "violations": list(decision.violations),
        "recommendations": list(decision.recommendations),
        "matched_rules": list(decision.matched_rules),
    }


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Usage: master certification <validate|check> [options]")
        return 2
    parser = build_parser()
    namespace = parser.parse_args(args)
    if namespace.command == "validate":
        return run_validate(namespace.policy_path, output_format=namespace.format)
    if namespace.command == "check":
        return run_check(
            namespace.policy_path,
            output_format=namespace.format,
            strict=namespace.strict,
            target_path=namespace.target,
            use_runtime=namespace.runtime,
            plugin_id=namespace.plugin,
            show_history=namespace.history,
        )
    if namespace.command == "runtime-status":
        return run_runtime_status(
            output_format=namespace.format,
            verbose=namespace.verbose,
            reload=namespace.reload,
            policy_path=namespace.policy,
        )
    return 2


def _default_policy_path() -> str:
    candidate = Path.cwd() / ".master_engine" / "certification_policy.json"
    if candidate.exists():
        return str(candidate)
    msg = "policy path is required when default policy file is missing"
    raise PolicyLoadError(msg)


def _load_target(target_path: str | None) -> dict[str, Any]:
    if target_path is None:
        return {
            "manifest": {"name": "health", "version": "1.0.0"},
            "source": "sdk module",
        }
    path = Path(target_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = "target file must contain a JSON object"
        raise PolicyLoadError(msg)
    return data


def _print_result(payload: dict[str, object], *, output_format: str, title: str) -> None:
    print(f"[MASTER ENGINE] {title}")
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for key, value in payload.items():
        if isinstance(value, list):
            joined = ", ".join(str(item) for item in value) if value else "(none)"
            print(f"  {key}: {joined}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
