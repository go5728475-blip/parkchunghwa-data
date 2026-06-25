"""Application-layer result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ResultError(Exception):
    """Raised when unwrapping a failed result or unwrapping error on success."""


@dataclass(frozen=True, kw_only=True)
class ErrorDetail:
    """Application-layer error detail."""

    code: str
    message: str
    context: dict[str, Any] | None = None


@dataclass(frozen=True)
class Success(Generic[T]):
    """Successful result carrying a value."""

    value: T

    @property
    def is_success(self) -> bool:
        return True

    @property
    def is_failure(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_error(self) -> ErrorDetail:
        msg = "Cannot unwrap error from a successful result."
        raise ResultError(msg)


@dataclass(frozen=True)
class Failure:
    """Failed result carrying error details."""

    error: ErrorDetail

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True

    def unwrap(self) -> Any:
        msg = f"Cannot unwrap failed result: {self.error.message}"
        raise ResultError(msg)

    def unwrap_error(self) -> ErrorDetail:
        return self.error


class Result:
    """Factory for application-layer success and failure values."""

    @staticmethod
    def ok(value: T) -> Success[T]:
        return Success(value=value)

    @staticmethod
    def fail(
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> Failure:
        return Failure(error=ErrorDetail(code=code, message=message, context=details))


ResultValue = Success[T] | Failure
