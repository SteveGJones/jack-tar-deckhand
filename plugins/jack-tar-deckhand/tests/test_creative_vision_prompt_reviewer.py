"""Tests for the Prompt Reviewer dispatch helper."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.prompt_reviewer import (  # noqa: E402
    build_reviewer_input,
    parse_reviewer_output,
)


def test_build_reviewer_input_includes_prose_and_prompt():
    blob = build_reviewer_input(
        original_prose="Four warships.",
        proposed_prompt="Render four warships in a battle.",
        parsed_vision={"original_prose": "Four warships."},
    )
    assert "Four warships." in blob
    assert "Render four warships in a battle." in blob


def test_parse_reviewer_output_pass_verdict():
    response = '```json\n{"verdict": "pass", "issues": []}\n```'
    verdict, issues = parse_reviewer_output(response)
    assert verdict == "pass"
    assert issues == []


def test_parse_reviewer_output_refine_with_issues():
    response = '```json\n{"verdict": "refine", "issues": ["Databricks ship label missing"]}\n```'
    verdict, issues = parse_reviewer_output(response)
    assert verdict == "refine"
    assert issues == ["Databricks ship label missing"]


def test_parse_reviewer_output_rejects_invalid_verdict():
    response = '```json\n{"verdict": "maybe", "issues": []}\n```'
    with pytest.raises(ValueError):
        parse_reviewer_output(response)
