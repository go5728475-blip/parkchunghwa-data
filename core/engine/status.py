"""Engine lifecycle status."""

from __future__ import annotations

from enum import StrEnum


class EngineStatus(StrEnum):
    """Lifecycle states for the engine kernel."""

    IDLE = "IDLE"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
