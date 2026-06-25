"""Tests for application result types."""

from __future__ import annotations

import pytest

from core.application.result import ErrorDetail, Failure, Result, ResultError, Success


def test_result_ok_success_path() -> None:
    result = Result.ok("value")
    assert isinstance(result, Success)
    assert result.is_success
    assert not result.is_failure
    assert result.unwrap() == "value"


def test_result_fail_failure_path() -> None:
    result = Result.fail("ERR", "something went wrong", details={"key": "val"})
    assert isinstance(result, Failure)
    assert result.is_failure
    assert not result.is_success
    error = result.unwrap_error()
    assert isinstance(error, ErrorDetail)
    assert error.code == "ERR"
    assert error.message == "something went wrong"
    assert error.context == {"key": "val"}


def test_success_unwrap_error_raises() -> None:
    with pytest.raises(ResultError):
        Result.ok(1).unwrap_error()


def test_failure_unwrap_raises() -> None:
    with pytest.raises(ResultError):
        Result.fail("ERR", "failed").unwrap()
