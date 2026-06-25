"""Tests for analysis explanation domain models."""

from __future__ import annotations

import pytest

from core.domain.ids import ExplanationId, SectionId
from core.domain.models import AnalysisExplanation, GeneratedBy
from core.domain.xai import build_plugin_explanation


def test_plugin_explanation_has_reasoning_and_evidence() -> None:
    section_id = SectionId.new()
    explanation = build_plugin_explanation(
        section_id=section_id,
        capability="wealth.analysis",
        plugin_id="wealth.stub",
        content="wealth placeholder",
    )

    assert explanation.generated_by is GeneratedBy.PLUGIN
    assert explanation.reasoning
    assert explanation.evidence
    assert explanation.section_id == section_id


def test_confidence_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValueError, match="Confidence"):
        AnalysisExplanation(
            explanation_id=ExplanationId.new(),
            section_id=SectionId.new(),
            confidence=1.5,
            reasoning=("step",),
            evidence=("item",),
            generated_by=GeneratedBy.PLUGIN,
        )


def test_confidence_accepts_valid_range() -> None:
    explanation = build_plugin_explanation(
        section_id=SectionId.new(),
        capability="career.analysis",
        plugin_id="career.stub",
        content="career placeholder",
    )

    assert 0.0 <= explanation.confidence <= 1.0
