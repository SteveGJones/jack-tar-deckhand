"""Tests for the Director's Brief dispatch helper (input/output marshalling)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.brief import build_brief_input, parse_brief_output  # noqa: E402


def test_build_brief_input_includes_prose_verbatim():
    input_blob = build_brief_input(
        vision_prose="Four warships SAP/Databricks/OpenAI/Anthropic.",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="ollama",
        brand_fidelity="none",
    )
    assert "Four warships SAP/Databricks/OpenAI/Anthropic." in input_blob


def test_build_brief_input_includes_tier_and_brand_fidelity():
    blob = build_brief_input(
        vision_prose="x",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="flash_2k",
        brand_fidelity="exact",
    )
    assert "flash_2k" in blob
    assert "exact" in blob


def test_build_brief_input_carries_feedback():
    blob = build_brief_input(
        vision_prose="x",
        prior_parsed_vision=None,
        accumulated_feedback=["Databricks ship missing", "ensure 4 labels visible"],
        current_tier="ollama",
        brand_fidelity="none",
    )
    assert "Databricks ship missing" in blob
    assert "ensure 4 labels visible" in blob


def test_parse_brief_output_extracts_parsed_vision_and_prompt():
    agent_response = """
```json
{
  "parsed_vision": {
    "schema_version": "1.0",
    "original_prose": "Four warships.",
    "prose_version": 1,
    "subjects": [],
    "spatial_directives": {"setting": null, "layout": null, "containment": null, "named_relationships": []},
    "style": {"explicit": null, "implied": null, "register_inherited_from": null},
    "composition": {"progression_axis": null, "primary_focus": null, "compositional_rules": []},
    "delivery": {"scale": "screen_16x9", "aspect": "16:9", "viewing_context": "projection"},
    "text_density_warning": {"estimated_text_elements": 0, "threshold_breach": false}
  },
  "prompt": "Render four warships..."
}
```
"""
    pv, prompt = parse_brief_output(agent_response)
    assert pv["original_prose"] == "Four warships."
    assert prompt == "Render four warships..."


def test_parse_brief_output_raises_on_missing_keys():
    with pytest.raises(ValueError):
        parse_brief_output('```json\n{"parsed_vision": {}}\n```')


def test_parse_brief_output_raises_on_non_canonical_parsed_vision_shape():
    """F1 from 2026-05-22 dogfood — Brief sometimes returns subjects as plain strings
    instead of {name, role, spatial_slot} objects. The parser must reject this."""
    agent_response = """
```json
{
  "parsed_vision": {
    "schema_version": "1.0",
    "original_prose": "Four warships.",
    "prose_version": 1,
    "subjects": ["SAP warship", "Databricks warship"],
    "spatial_directives": {"setting": null, "layout": null, "containment": null, "named_relationships": []},
    "style": {"explicit": null, "implied": null, "register_inherited_from": null},
    "composition": {"progression_axis": null, "primary_focus": null, "compositional_rules": []},
    "delivery": {"scale": "screen_16x9", "aspect": "16:9", "viewing_context": "projection"},
    "text_density_warning": {"estimated_text_elements": 0, "threshold_breach": false}
  },
  "prompt": "Render four warships..."
}
```
"""
    with pytest.raises(ValueError, match="failed schema"):
        parse_brief_output(agent_response)


def test_parse_brief_output_raises_on_missing_required_parsed_vision_key():
    """ParsedVision missing a required top-level key (text_density_warning here) must fail."""
    agent_response = """
```json
{
  "parsed_vision": {
    "schema_version": "1.0",
    "original_prose": "x",
    "prose_version": 1,
    "subjects": [],
    "spatial_directives": {"setting": null, "layout": null, "containment": null, "named_relationships": []},
    "style": {"explicit": null, "implied": null, "register_inherited_from": null},
    "composition": {"progression_axis": null, "primary_focus": null, "compositional_rules": []},
    "delivery": {"scale": "screen_16x9", "aspect": "16:9", "viewing_context": "projection"}
  },
  "prompt": "..."
}
```
"""
    with pytest.raises(ValueError, match="failed schema"):
        parse_brief_output(agent_response)


def test_parse_brief_output_raises_on_empty_prompt():
    """Brief returning an empty / whitespace prompt is a contract violation."""
    agent_response = """
```json
{
  "parsed_vision": {
    "schema_version": "1.0",
    "original_prose": "x",
    "prose_version": 1,
    "subjects": [],
    "spatial_directives": {"setting": null, "layout": null, "containment": null, "named_relationships": []},
    "style": {"explicit": null, "implied": null, "register_inherited_from": null},
    "composition": {"progression_axis": null, "primary_focus": null, "compositional_rules": []},
    "delivery": {"scale": "screen_16x9", "aspect": "16:9", "viewing_context": "projection"},
    "text_density_warning": {"estimated_text_elements": 0, "threshold_breach": false}
  },
  "prompt": "   "
}
```
"""
    with pytest.raises(ValueError, match="non-empty"):
        parse_brief_output(agent_response)
