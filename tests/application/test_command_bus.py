"""Tests for command bus."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from core.application.command_bus import CommandBus
from core.application.result import Failure, Result, Success
from core.contracts.command import Command
from core.contracts.metadata import Metadata


@dataclass(frozen=True, kw_only=True)
class SampleCommand(Command):
  value: str


def test_command_bus_register_and_dispatch() -> None:
    bus = CommandBus()

    def handler(command: SampleCommand) -> Result[str]:
        return Result.ok(command.value.upper())

    bus.register(SampleCommand, handler)
    result = bus.dispatch(
        SampleCommand(metadata=Metadata(correlation_id=uuid4()), value="hello"),
    )

    assert isinstance(result, Success)
    assert result.unwrap() == "HELLO"


def test_command_bus_missing_handler_returns_failure() -> None:
    bus = CommandBus()
    result = bus.dispatch(
        SampleCommand(metadata=Metadata(correlation_id=uuid4()), value="x"),
    )
    assert isinstance(result, Failure)
    assert result.error.code == "HANDLER_NOT_FOUND"


def test_command_bus_handler_exception_returns_failure() -> None:
    bus = CommandBus()

    def handler(_command: SampleCommand) -> Result[str]:
        msg = "boom"
        raise RuntimeError(msg)

    bus.register(SampleCommand, handler)
    result = bus.dispatch(
        SampleCommand(metadata=Metadata(correlation_id=uuid4()), value="x"),
    )
    assert isinstance(result, Failure)
    assert result.error.code == "HANDLER_ERROR"
    assert "boom" in result.error.message
