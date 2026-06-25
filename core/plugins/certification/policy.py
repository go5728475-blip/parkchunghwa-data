"""Certification policy for registered plugins."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True, kw_only=True)
class PolicyResult:
    """Outcome of a certification policy evaluation."""

    allowed: bool
    reasons: tuple[str, ...] = ()


@dataclass
class CertificationPolicy:
    """Evaluates whether a registered plugin record remains valid for loading."""

    max_age_days: int = 30
    require_same_version: bool = True

    def evaluate(
        self,
        record: object,
        *,
        plugin: object | None = None,
    ) -> PolicyResult:
        reasons: list[str] = []

        if not record.certified:
            reasons.append("plugin is not certified")

        if self.require_same_version and plugin is not None:
            current_version = _plugin_version(plugin)
            if record.version != current_version:
                reasons.append(
                    f"version mismatch: registry={record.version}, plugin={current_version}",
                )

        certified_at = _coerce_datetime(record.certified_at)
        age = datetime.now(UTC) - certified_at
        if age > timedelta(days=self.max_age_days):
            reasons.append(
                f"certification expired: age {age.days} days exceeds {self.max_age_days}",
            )

        if reasons:
            return PolicyResult(allowed=False, reasons=tuple(reasons))
        return PolicyResult(allowed=True)


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


def _coerce_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
