"""Tests for plugin certification framework."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from core.plugins.certification.checks import (
    CapabilityDeclarationCheck,
    LifecycleCheck,
    ManifestRequiredCheck,
    ProviderIndependenceCheck,
    SDKVersionCheck,
)
from core.plugins.certification.factory import create_default_plugin_certification_suite
from core.plugins.certification.result import PluginCertificationResult
from core.plugins.certification.suite import PluginCertificationSuite
from sdk.manifest import PluginManifest
from sdk.version import PLUGIN_SDK_VERSION


@dataclass(frozen=True, kw_only=True)
class _Manifest:
    name: str
    version: str
    capabilities: tuple[str, ...]
    sdk_version: str | None = None


class _ValidPlugin:
    manifest = _Manifest(
        name="wealth",
        version="1.0.0",
        capabilities=("wealth.analysis",),
        sdk_version=PLUGIN_SDK_VERSION,
    )

    def name(self) -> str:
        return self.manifest.name

    def boot(self, container: object | None = None) -> None:
        return None

    def shutdown(self, container: object | None = None) -> None:
        return None


class _MissingManifestPlugin:
    def name(self) -> str:
        return "anonymous"

    def boot(self) -> None:
        return None

    def shutdown(self) -> None:
        return None


class _MissingNameManifestPlugin:
    manifest = _Manifest(
        name="",
        version="1.0.0",
        capabilities=("wealth.analysis",),
    )

    def boot(self) -> None:
        return None

    def shutdown(self) -> None:
        return None


class _MissingBootPlugin:
    manifest = _Manifest(
        name="career",
        version="1.0.0",
        capabilities=("career.analysis",),
    )

    def shutdown(self) -> None:
        return None


class _MissingShutdownPlugin:
    manifest = _Manifest(
        name="career",
        version="1.0.0",
        capabilities=("career.analysis",),
    )

    def boot(self) -> None:
        return None


class _EmptyCapabilitiesPlugin:
    manifest = _Manifest(
        name="relationship",
        version="1.0.0",
        capabilities=(),
    )

    def boot(self) -> None:
        return None

    def shutdown(self) -> None:
        return None


class _IncompatibleSdkPlugin:
    manifest = _Manifest(
        name="health",
        version="1.0.0",
        capabilities=("health.analysis",),
        sdk_version="2.0.0",
    )

    def boot(self) -> None:
        return None

    def shutdown(self) -> None:
        return None


class _OpenAIReferencedPlugin:
    """Uses openai provider in implementation."""

    manifest = _Manifest(
        name="provider_bound",
        version="1.0.0",
        capabilities=("provider_bound.analysis",),
    )

    def boot(self) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def execute(self) -> str:
        return "openai client integration"


class _ExplodingCheck:
    name = "exploding"

    def check(self, plugin: object) -> PluginCertificationResult:
        raise RuntimeError("boom")


def test_valid_plugin_passes_default_suite() -> None:
    result = create_default_plugin_certification_suite().certify(_ValidPlugin())

    assert result.passed is True
    assert not result.errors
    assert "manifest_required" in result.checks
    assert "lifecycle" in result.checks


def test_missing_manifest_fails() -> None:
    result = ManifestRequiredCheck().check(_MissingManifestPlugin())

    assert result.passed is False
    assert any("manifest is required" in error.lower() for error in result.errors)


def test_manifest_missing_name_fails() -> None:
    result = ManifestRequiredCheck().check(_MissingNameManifestPlugin())

    assert result.passed is False
    assert any("name is required" in error.lower() for error in result.errors)


def test_missing_boot_fails_lifecycle_check() -> None:
    result = LifecycleCheck().check(_MissingBootPlugin())

    assert result.passed is False
    assert any("boot()" in error for error in result.errors)


def test_missing_shutdown_fails_lifecycle_check() -> None:
    result = LifecycleCheck().check(_MissingShutdownPlugin())

    assert result.passed is False
    assert any("shutdown()" in error for error in result.errors)


def test_empty_capabilities_fail() -> None:
    result = CapabilityDeclarationCheck().check(_EmptyCapabilitiesPlugin())

    assert result.passed is False
    assert any("empty" in error.lower() for error in result.errors)


def test_sdk_version_compatible_passes() -> None:
    result = SDKVersionCheck().check(_ValidPlugin())

    assert result.passed is True


def test_sdk_version_incompatible_fails() -> None:
    result = SDKVersionCheck().check(_IncompatibleSdkPlugin())

    assert result.passed is False
    assert any("Incompatible sdk_version" in error for error in result.errors)


def test_provider_hardcoded_plugin_emits_warning_only() -> None:
    result = ProviderIndependenceCheck().check(_OpenAIReferencedPlugin())

    assert result.passed is True
    assert result.warnings
    assert any("openai" in warning.lower() for warning in result.warnings)


def test_multiple_errors_merge_in_suite() -> None:
    suite = PluginCertificationSuite(
        checks=[ManifestRequiredCheck(), LifecycleCheck()],
    )

    result = suite.certify(_MissingManifestPlugin())

    assert result.passed is False
    assert len(result.errors) >= 1
    assert "manifest_required" in result.checks


def test_check_exception_becomes_certification_error() -> None:
    suite = PluginCertificationSuite(checks=[_ExplodingCheck()])

    result = suite.certify(_ValidPlugin())

    assert result.passed is False
    assert any("certification error" in error for error in result.errors)


def test_default_factory_contains_all_checks() -> None:
    suite = create_default_plugin_certification_suite()
    result = suite.certify(_ValidPlugin())

    assert result.checks == (
        "manifest_required",
        "lifecycle",
        "capability_declaration",
        "sdk_version",
        "provider_independence",
    )


def test_result_merge_accumulates_fields() -> None:
    first = PluginCertificationResult.pass_result("wealth", checks=("a",))
    second = PluginCertificationResult.fail_result(
        "wealth",
        errors=("failed",),
        warnings=("warn",),
        checks=("b",),
    )

    merged = first.merge(second)

    assert merged.passed is False
    assert merged.errors == ("failed",)
    assert merged.warnings == ("warn",)
    assert merged.checks == ("a", "b")


def test_pass_and_fail_result_helpers() -> None:
    passed = PluginCertificationResult.pass_result("wealth", checks=("manifest_required",))
    failed = PluginCertificationResult.fail_result("wealth", errors=("missing manifest",))

    assert passed.passed is True
    assert failed.passed is False

    with pytest.raises(ValueError, match="cannot be passed"):
        PluginCertificationResult(
            plugin_id="wealth",
            passed=True,
            errors=("conflict",),
        )
