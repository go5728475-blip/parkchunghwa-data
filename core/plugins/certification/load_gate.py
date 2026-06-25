"""Certification gate helpers for module loading."""

from __future__ import annotations

from core.plugins.certification.gate import CertificationGate
from core.plugins.certification.result import PluginCertificationResult
from core.plugins.registry.certified import CertifiedPluginRecord


class PluginCertificationError(Exception):
    """Raised when plugin certification blocks loading."""

    def __init__(self, result: PluginCertificationResult) -> None:
        self.result = result
        errors = ", ".join(result.errors) if result.errors else "certification failed"
        msg = f"Plugin certification failed for {result.plugin_id}: {errors}"
        super().__init__(msg)


def certify_plugin_before_load(
    plugin: object,
    gate: CertificationGate | None = None,
    *,
    require_registered: bool = False,
    registry: object | None = None,
    container: object | None = None,
    policy: object | None = None,
) -> CertifiedPluginRecord:
    """Certify a plugin and register the outcome before runtime load."""
    resolved_registry = registry
    if resolved_registry is None:
        if gate is not None:
            resolved_registry = gate.registry
        else:
            from core.plugins.registry.resolver import resolve_certified_registry

            resolved_registry = resolve_certified_registry(container)

    certification_gate = gate or CertificationGate(registry=resolved_registry)
    result = certification_gate.evaluate(plugin)
    if certification_gate.strict and not result.passed:
        raise PluginCertificationError(result)

    if require_registered:
        if registry is None:
            raise PluginCertificationError(
                PluginCertificationResult.fail_result(
                    result.plugin_id,
                    errors=("certified plugin registry is required",),
                ),
            )
        if not registry.is_certified(result.plugin_id):
            raise PluginCertificationError(
                PluginCertificationResult.fail_result(
                    result.plugin_id,
                    errors=(f"plugin {result.plugin_id} is not registered as certified",),
                ),
            )
        record = registry.get(result.plugin_id)
        if record is None:
            raise PluginCertificationError(
                PluginCertificationResult.fail_result(
                    result.plugin_id,
                    errors=(f"plugin {result.plugin_id} is not registered as certified",),
                ),
            )
        from core.plugins.certification.policy import CertificationPolicy

        active_policy = policy or CertificationPolicy()
        policy_result = active_policy.evaluate(record, plugin=plugin)
        if not policy_result.allowed:
            raise PluginCertificationError(
                PluginCertificationResult.fail_result(
                    result.plugin_id,
                    errors=policy_result.reasons,
                ),
            )

    return certification_gate.certify_and_register(plugin, result=result)
