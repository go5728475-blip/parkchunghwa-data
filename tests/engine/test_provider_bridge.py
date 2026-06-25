"""Tests for engine provider bridge during RunAnalysis."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.application.commands import RunAnalysis
from core.application.result import Failure, Success
from core.bootstrap.bootstrap import Bootstrap
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId
from core.domain.models import SectionSource, TraceStep
from core.domain.value_objects import BirthData, EngineContext


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _run_analysis_command(
    *,
    capability: str = "stub.analysis",
    provider_id: str | None = None,
) -> RunAnalysis:
    user_id = UserId.new()
    session_id = SessionId.new()
    return RunAnalysis(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1992, month=4, day=4, hour=4, minute=4),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability=capability,
        provider_id=ProviderId(value=provider_id) if provider_id else None,
    )


@pytest.mark.parametrize(
    ("provider_id", "placeholder"),
    [
        ("openai.stub", "openai stub placeholder response"),
        ("claude.stub", "claude stub placeholder response"),
    ],
)
def test_run_analysis_with_provider_id_success(provider_id: str, placeholder: str) -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _run_analysis_command(provider_id=provider_id),
    )

    assert isinstance(result, Success)
    analysis_result = result.unwrap().analysis_result
    assert analysis_result is not None
    assert len(analysis_result.sections) == 2
    assert analysis_result.sections[0].source is SectionSource.PLUGIN
    assert analysis_result.sections[1].source is SectionSource.PROVIDER
    assert placeholder in analysis_result.sections[1].content


def test_provider_result_in_report_section() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _run_analysis_command(provider_id="openai.stub"),
    )

    assert isinstance(result, Success)
    report = bootstrap.unit_of_work().reports.get(result.unwrap().report_id)
    assert report is not None
    assert len(report.sections) == 2
    assert report.sections[0].content == "stub placeholder"
    assert "openai stub placeholder response" in report.sections[1].content


def test_provider_result_in_explanation_trace() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _run_analysis_command(provider_id="openai.stub"),
    )

    assert isinstance(result, Success)
    analysis_result = result.unwrap().analysis_result
    assert analysis_result is not None
    steps = [entry.step for entry in analysis_result.trace]
    assert steps[0] is TraceStep.PLUGIN
    assert steps[1] is TraceStep.PROVIDER
    assert steps[2] is TraceStep.REPORT
    assert analysis_result.trace[0].source == "stub.analysis"
    assert str(analysis_result.trace[1].source) == "openai.stub"


def test_run_analysis_missing_provider_id_failure() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _run_analysis_command(provider_id="missing.provider"),
    )

    assert isinstance(result, Failure)
    assert result.error.code == "PROVIDER_NOT_FOUND"
    assert "missing.provider" in result.error.message


def test_run_analysis_without_provider_id_uses_plugin_flow() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(_run_analysis_command())

    assert isinstance(result, Success)
    analysis_result = result.unwrap().analysis_result
    assert analysis_result is not None
    assert len(analysis_result.sections) == 1
    assert analysis_result.sections[0].source is SectionSource.PLUGIN
    assert analysis_result.trace[0].step is TraceStep.PLUGIN
    assert analysis_result.trace[0].source == "stub.analysis"
