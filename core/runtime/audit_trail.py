"""Certification policy runtime audit trail."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class AuditEventType(StrEnum):
    """Certification runtime audit event types."""

    POLICY_LOADED = "POLICY_LOADED"
    POLICY_VALIDATED = "POLICY_VALIDATED"
    POLICY_ENFORCED = "POLICY_ENFORCED"
    POLICY_FAILED = "POLICY_FAILED"


@dataclass(frozen=True, kw_only=True)
class PolicyAuditEntry:
    """Audit record for certification runtime events."""

    timestamp: str
    event: str
    plugin_id: str | None
    policy_id: str
    decision: str | None = None
    violations: tuple[str, ...] = ()


class CertificationAuditTrail:
    """In-memory audit trail for certification runtime events."""

    def __init__(self) -> None:
        self._entries: list[PolicyAuditEntry] = []

    def record(
        self,
        event: AuditEventType | str,
        *,
        policy_id: str,
        plugin_id: str | None = None,
        decision: str | None = None,
        violations: tuple[str, ...] = (),
    ) -> PolicyAuditEntry:
        entry = PolicyAuditEntry(
            timestamp=datetime.now(UTC).isoformat(),
            event=str(event),
            plugin_id=plugin_id,
            policy_id=policy_id,
            decision=decision,
            violations=violations,
        )
        self._entries.append(entry)
        return entry

    def history(self) -> tuple[PolicyAuditEntry, ...]:
        return tuple(self._entries)

    def clear(self) -> None:
        self._entries.clear()
