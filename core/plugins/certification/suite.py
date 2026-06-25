"""Plugin certification suite."""

from __future__ import annotations

from core.plugins.certification.interfaces import PluginCertificationCheck
from core.plugins.certification.result import PluginCertificationResult


class PluginCertificationSuite:
    """Runs registered certification checks against a plugin."""

    def __init__(self, checks: list[PluginCertificationCheck] | None = None) -> None:
        self._checks: list[PluginCertificationCheck] = list(checks or [])

    def register_check(self, check: PluginCertificationCheck) -> None:
        self._checks.append(check)

    def certify(self, plugin: object) -> PluginCertificationResult:
        plugin_id = _resolve_plugin_id(plugin)
        result = PluginCertificationResult.pass_result(plugin_id)

        for check in self._checks:
            try:
                check_result = check.check(plugin)
            except Exception as exc:  # noqa: BLE001
                check_result = PluginCertificationResult.fail_result(
                    plugin_id,
                    errors=(f"{check.name}: certification error: {exc}",),
                    checks=(check.name,),
                )
            result = result.merge(check_result)

        return result


def _resolve_plugin_id(plugin: object) -> str:
    manifest = getattr(plugin, "manifest", None)
    if manifest is not None:
        name = getattr(manifest, "name", None)
        if name:
            return str(name)

    name_attr = getattr(plugin, "name", None)
    if callable(name_attr):
        return str(name_attr())
    if isinstance(name_attr, str) and name_attr:
        return name_attr

    return plugin.__class__.__name__
