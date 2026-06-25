"""Tests for persistent registry audit store."""

from __future__ import annotations

import json
from pathlib import Path

from core.plugins.registry.audit import RegistryAuditEntry, RegistryAuditLogger
from core.plugins.registry.audit_json_store import JsonRegistryAuditStore


def _entry(*, plugin_id: str, action: str = "register") -> RegistryAuditEntry:
    return RegistryAuditEntry(
        timestamp="2026-01-01T00:00:00+00:00",
        action=action,
        plugin_id=plugin_id,
        version="1.0.0",
        result="success",
    )


def test_append_persists(tmp_path: Path) -> None:
    store = JsonRegistryAuditStore(tmp_path / "audit.json")

    store.append(_entry(plugin_id="wealth"))

    data = json.loads((tmp_path / "audit.json").read_text(encoding="utf-8"))
    assert len(data["entries"]) == 1
    assert data["entries"][0]["plugin_id"] == "wealth"


def test_load_persists(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "timestamp": "2026-01-01T00:00:00+00:00",
                        "action": "register",
                        "plugin_id": "career",
                        "version": "0.1.0",
                        "result": "success",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    store = JsonRegistryAuditStore(audit_path)

    entries = store.load_all()

    assert len(entries) == 1
    assert entries[0].plugin_id == "career"


def test_clear_persists(tmp_path: Path) -> None:
    store = JsonRegistryAuditStore(tmp_path / "audit.json")
    store.append(_entry(plugin_id="health"))

    store.clear()

    data = json.loads((tmp_path / "audit.json").read_text(encoding="utf-8"))
    assert data["entries"] == []


def test_logger_restores_history(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.json"
    first_logger = RegistryAuditLogger(store=JsonRegistryAuditStore(audit_path))
    first_logger.record_register("study", "0.1.0")

    second_logger = RegistryAuditLogger(store=JsonRegistryAuditStore(audit_path))
    entries = second_logger.list_entries()

    assert len(entries) == 1
    assert entries[0].plugin_id == "study"
    assert entries[0].action == "register"
