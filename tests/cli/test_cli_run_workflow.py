"""Tests for run-workflow CLI command."""

from __future__ import annotations

import json

from core.cli.main import run_workflow


def test_cli_run_workflow_default_capabilities(capsys) -> None:
    exit_code = run_workflow()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Workflow Summary" in captured.out
    assert "wealth.analysis" in captured.out
    assert "career.analysis" in captured.out
    assert "relationship.analysis" in captured.out
    assert "Capability Results:" in captured.out
    assert "Trace:" in captured.out


def test_cli_run_workflow_custom_capabilities(capsys) -> None:
    exit_code = run_workflow(
        capabilities=("wealth.analysis", "career.analysis"),
        provider_id="openai.stub",
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[wealth.analysis]" in captured.out
    assert "[career.analysis]" in captured.out
    assert "openai enrichment" in captured.out.lower() or "enrichment" in captured.out.lower()


def test_cli_run_workflow_plugin_only(capsys) -> None:
    exit_code = run_workflow(capabilities=("stub.analysis",), provider_id=None)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Plugin 1개" in captured.out


def test_cli_run_workflow_export_json(capsys) -> None:
    exit_code = run_workflow(
        capabilities=("wealth.analysis",),
        provider_id="openai.stub",
        export_format="json",
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["sections"]
    assert payload["trace"]
