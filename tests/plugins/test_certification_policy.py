"""Tests for certification policy."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.certification.policy import CertificationPolicy
from core.plugins.registry.certified import CertifiedPluginRecord
from tests.plugins.test_plugin_certification import _ValidPlugin


def _record(
    *,
    plugin_id: str = "wealth",
    version: str = "1.0.0",
    certified: bool = True,
    certified_at: datetime | None = None,
) -> CertifiedPluginRecord:
    return CertifiedPluginRecord(
        plugin_id=plugin_id,
        version=version,
        compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
        certified=certified,
        certified_at=certified_at or datetime.now(UTC),
    )


def test_valid_record_allowed() -> None:
    policy = CertificationPolicy()
    plugin = _ValidPlugin()

    result = policy.evaluate(_record(version="1.0.0"), plugin=plugin)

    assert result.allowed is True
    assert not result.reasons


def test_uncertified_blocked() -> None:
    policy = CertificationPolicy()

    result = policy.evaluate(_record(certified=False))

    assert result.allowed is False
    assert any("not certified" in reason for reason in result.reasons)


def test_version_mismatch_blocked() -> None:
    policy = CertificationPolicy()
    plugin = _ValidPlugin()

    result = policy.evaluate(_record(version="9.9.9"), plugin=plugin)

    assert result.allowed is False
    assert any("version mismatch" in reason for reason in result.reasons)


def test_expired_certification_blocked() -> None:
    policy = CertificationPolicy(max_age_days=30)
    expired_at = datetime.now(UTC) - timedelta(days=31)

    result = policy.evaluate(_record(certified_at=expired_at))

    assert result.allowed is False
    assert any("expired" in reason for reason in result.reasons)


def test_custom_max_age() -> None:
    policy = CertificationPolicy(max_age_days=7)
    expired_at = datetime.now(UTC) - timedelta(days=8)

    result = policy.evaluate(_record(certified_at=expired_at))

    assert result.allowed is False
    assert any("7" in reason for reason in result.reasons)

    recent_at = datetime.now(UTC) - timedelta(days=3)
    allowed = policy.evaluate(_record(certified_at=recent_at))

    assert allowed.allowed is True
