"""Analysis session aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from core.domain.aggregate import AggregateRoot
from core.domain.events import AnalysisSessionCreated
from core.domain.ids import AggregateId, SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext


class SessionStatus(StrEnum):
    """Lifecycle states for an analysis session."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


_TERMINAL_STATUSES = frozenset({SessionStatus.COMPLETED, SessionStatus.FAILED})


@dataclass
class AnalysisSession(AggregateRoot):
    """Aggregate root for a single analysis session."""

    session_id: SessionId
    user_id: UserId
    birth_data: BirthData
    context: EngineContext
    status: SessionStatus = field(default=SessionStatus.CREATED)

    @classmethod
    def create(
        cls,
        user_id: UserId,
        birth_data: BirthData,
        context: EngineContext,
    ) -> AnalysisSession:
        """Create a new analysis session in CREATED state."""
        session_id = SessionId.new()
        session = cls(
            id=AggregateId(str(session_id)),
            session_id=session_id,
            user_id=user_id,
            birth_data=birth_data,
            context=context,
        )
        session.record_event(
            AnalysisSessionCreated(
                aggregate_id=str(session_id),
                metadata={
                    "user_id": str(user_id),
                    "session_id": str(session_id),
                },
                payload={
                    "user_id": str(user_id),
                    "session_id": str(session_id),
                },
            ),
        )
        return session

    def mark_running(self) -> None:
        """Transition session to RUNNING."""
        if self.status in _TERMINAL_STATUSES:
            msg = f"Cannot move to RUNNING from terminal status {self.status}."
            raise ValueError(msg)
        if self.status == SessionStatus.RUNNING:
            msg = "Session is already RUNNING."
            raise ValueError(msg)
        self.status = SessionStatus.RUNNING

    def mark_completed(self) -> None:
        """Transition session to COMPLETED."""
        if self.status == SessionStatus.COMPLETED:
            msg = "Session is already COMPLETED."
            raise ValueError(msg)
        if self.status == SessionStatus.FAILED:
            msg = "Cannot complete a FAILED session."
            raise ValueError(msg)
        if self.status != SessionStatus.RUNNING:
            msg = f"Cannot complete session from status {self.status}."
            raise ValueError(msg)
        self.status = SessionStatus.COMPLETED

    def mark_failed(self, reason: str) -> None:
        """Transition session to FAILED with a reason."""
        if not reason or not reason.strip():
            msg = "Failure reason is required."
            raise ValueError(msg)
        if self.status in _TERMINAL_STATUSES:
            msg = f"Cannot fail session from terminal status {self.status}."
            raise ValueError(msg)
        self.status = SessionStatus.FAILED
