"""Plugin certification result model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class PluginCertificationResult:
    """Aggregated outcome of plugin certification checks."""

    plugin_id: str
    passed: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    checks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.errors and self.passed:
            msg = "Certification result cannot be passed when errors are present."
            raise ValueError(msg)

    @classmethod
    def pass_result(
        cls,
        plugin_id: str,
        checks: tuple[str, ...] = (),
    ) -> PluginCertificationResult:
        return cls(plugin_id=plugin_id, passed=True, checks=checks)

    @classmethod
    def fail_result(
        cls,
        plugin_id: str,
        errors: tuple[str, ...],
        warnings: tuple[str, ...] = (),
        checks: tuple[str, ...] = (),
    ) -> PluginCertificationResult:
        return cls(
            plugin_id=plugin_id,
            passed=False,
            errors=errors,
            warnings=warnings,
            checks=checks,
        )

    def merge(self, other: PluginCertificationResult) -> PluginCertificationResult:
        errors = self.errors + other.errors
        warnings = self.warnings + other.warnings
        checks = self.checks + other.checks
        plugin_id = self.plugin_id or other.plugin_id
        passed = not errors
        return PluginCertificationResult(
            plugin_id=plugin_id,
            passed=passed,
            errors=errors,
            warnings=warnings,
            checks=checks,
        )
