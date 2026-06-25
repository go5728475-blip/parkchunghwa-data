"""Plugin certification gate."""

from __future__ import annotations

from datetime import UTC, datetime

from core.plugins.certification.compatibility import map_result_to_compatibility_level
from core.plugins.certification.factory import create_default_plugin_certification_suite
from core.plugins.certification.result import PluginCertificationResult
from core.plugins.certification.suite import PluginCertificationSuite


class CertificationGate:
    """Evaluates plugins and optionally records certification outcomes."""

    def __init__(
        self,
        suite: PluginCertificationSuite | None = None,
        registry: object | None = None,
        strict: bool = True,
    ) -> None:
        from core.plugins.registry.certified import CertifiedPluginRegistry

        self.suite = suite or create_default_plugin_certification_suite()
        self.registry = registry or CertifiedPluginRegistry()
        self.strict = strict

    def evaluate(self, plugin: object) -> PluginCertificationResult:
        return self.suite.certify(plugin)

    def allow(self, plugin: object) -> bool:
        return self._allow_result(self.evaluate(plugin))

    def certify_and_register(
        self,
        plugin: object,
        result: PluginCertificationResult | None = None,
    ) -> object:
        from core.plugins.registry.certified import CertifiedPluginRecord

        certification = result or self.evaluate(plugin)
        compatibility = map_result_to_compatibility_level(certification)
        certified = certification.passed
        record = CertifiedPluginRecord(
            plugin_id=certification.plugin_id,
            version=_plugin_version(plugin),
            compatibility_level=compatibility,
            certified=certified,
            warnings=certification.warnings,
            checks=certification.checks,
            certified_at=datetime.now(UTC),
        )
        self.registry.register(record)
        return record

    def _allow_result(self, result: PluginCertificationResult) -> bool:
        if self.strict:
            return result.passed
        return True


def _plugin_version(plugin: object) -> str:
    manifest = getattr(plugin, "manifest", None)
    if manifest is not None:
        version = getattr(manifest, "version", None)
        if version:
            return str(version)
    version_attr = getattr(plugin, "version", None)
    if callable(version_attr):
        return str(version_attr())
    if isinstance(version_attr, str) and version_attr:
        return version_attr
    return "0.0.0"
