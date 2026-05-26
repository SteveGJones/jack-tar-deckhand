"""Tests for the creative anchors module (#113 AC4)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.anchors import (  # noqa: E402
    anchors_for_slide,
    anchors_path,
    format_anchors_for_brief,
    load_anchors,
    lookup_anchor,
    validate_anchors,
)
from src.creative_vision.brief import build_brief_input  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _valid_anchors() -> dict:
    return {
        "schema_version": "1.0.0",
        "deck_brief": "1980s Wall Street cinematic style",
        "anchors": [
            {
                "name": "The Customer",
                "kind": "character",
                "description": (
                    "Mid-50s man, salt-and-pepper hair, tortoiseshell glasses, "
                    "navy double-breasted blazer with crested buttons"
                ),
                "appears_in_slides": [1, 3, 5],
                "negative_traits": ["beard"],
            },
            {
                "name": "The Sales Rep",
                "kind": "character",
                "description": "Late 20s woman in cream silk blouse and pearls",
                "appears_in_slides": [1, 2],
            },
            {
                "name": "Cocktail Napkin",
                "kind": "prop",
                "description": "Triangular wedge-shaped cocktail napkin",
            },
            {
                "name": "Period Palette",
                "kind": "style_anchor",
                "description": "Saturated 35mm film grain, deep amber + cyan + bronze",
            },
        ],
    }


def _write_anchors(deck_dir, anchors):
    path = anchors_path(str(deck_dir))
    with open(path, "w") as f:
        json.dump(anchors, f)


# ---------------------------------------------------------------------------
# load_anchors
# ---------------------------------------------------------------------------


def test_load_anchors_returns_none_when_file_absent(tmp_path):
    assert load_anchors(str(tmp_path)) is None


def test_load_anchors_returns_validated_dict(tmp_path):
    _write_anchors(tmp_path, _valid_anchors())
    loaded = load_anchors(str(tmp_path))
    assert loaded is not None
    assert loaded["schema_version"] == "1.0.0"
    assert len(loaded["anchors"]) == 4


def test_load_anchors_raises_on_bad_json(tmp_path):
    path = anchors_path(str(tmp_path))
    with open(path, "w") as f:
        f.write("not json {{")
    with pytest.raises(ValueError, match="failed to parse"):
        load_anchors(str(tmp_path))


def test_load_anchors_raises_on_schema_violation(tmp_path):
    bad = {
        "schema_version": "1.0.0",
        "anchors": [
            {"name": "X", "kind": "invalid_kind", "description": "x"},
        ],
    }
    _write_anchors(tmp_path, bad)
    with pytest.raises(ValueError, match="creative_anchors validation failed"):
        load_anchors(str(tmp_path))


def test_load_anchors_path_is_deck_dir_creative_anchors_json(tmp_path):
    """Pin the canonical filename — Brief integration relies on this path."""
    assert anchors_path(str(tmp_path)).endswith("creative_anchors.json")
    assert str(tmp_path) in anchors_path(str(tmp_path))


# ---------------------------------------------------------------------------
# validate_anchors
# ---------------------------------------------------------------------------


def test_validate_anchors_accepts_minimal_anchor():
    """Only schema_version + anchors array is required, and anchors can be empty."""
    validate_anchors({"schema_version": "1.0.0", "anchors": []})


def test_validate_anchors_rejects_missing_schema_version():
    with pytest.raises(ValueError, match=r"schema_version|/$"):
        validate_anchors({"anchors": []})


def test_validate_anchors_rejects_unknown_kind():
    bad = {
        "schema_version": "1.0.0",
        "anchors": [{"name": "x", "kind": "ghost", "description": "y"}],
    }
    with pytest.raises(ValueError, match=r"validation failed.*/anchors/0/kind"):
        validate_anchors(bad)


def test_validate_anchors_rejects_additional_properties_on_anchor():
    """``additionalProperties: false`` keeps anchors honest — typoed fields
    surface as schema errors rather than being silently dropped."""
    bad = {
        "schema_version": "1.0.0",
        "anchors": [
            {
                "name": "x",
                "kind": "character",
                "description": "y",
                "typoed_field": "oops",
            }
        ],
    }
    with pytest.raises(ValueError, match="validation failed"):
        validate_anchors(bad)


def test_validate_anchors_rejects_empty_description():
    bad = {
        "schema_version": "1.0.0",
        "anchors": [{"name": "x", "kind": "character", "description": ""}],
    }
    with pytest.raises(ValueError, match="validation failed"):
        validate_anchors(bad)


# ---------------------------------------------------------------------------
# lookup_anchor / anchors_for_slide
# ---------------------------------------------------------------------------


def test_lookup_anchor_case_sensitive_hit():
    anchors = _valid_anchors()
    a = lookup_anchor(anchors, "The Customer")
    assert a is not None
    assert a["kind"] == "character"


def test_lookup_anchor_returns_none_on_miss():
    assert lookup_anchor(_valid_anchors(), "Nonexistent") is None


def test_lookup_anchor_case_sensitive():
    """Operator-controlled names — 'the customer' and 'The Customer' are
    different anchors. The Brief must use the exact name."""
    assert lookup_anchor(_valid_anchors(), "the customer") is None


def test_anchors_for_slide_includes_deck_wide_anchors():
    """Anchors without appears_in_slides are eligible for every slide.

    Cocktail Napkin and Period Palette have no appears_in_slides; they must
    appear in every slide's result regardless of slide_number.
    """
    eligible = anchors_for_slide(_valid_anchors(), slide_number=99)
    names = [a["name"] for a in eligible]
    assert "Cocktail Napkin" in names
    assert "Period Palette" in names
    # The slide-specific anchors should NOT appear (slide 99 isn't in their lists)
    assert "The Customer" not in names
    assert "The Sales Rep" not in names


def test_anchors_for_slide_includes_specific_anchors():
    eligible = anchors_for_slide(_valid_anchors(), slide_number=3)
    names = [a["name"] for a in eligible]
    # The Customer appears in slide 3
    assert "The Customer" in names
    # The Sales Rep does NOT appear in slide 3
    assert "The Sales Rep" not in names
    # Deck-wide anchors always appear
    assert "Cocktail Napkin" in names


def test_anchors_for_slide_preserves_file_order():
    """Order matters — operator may rely on it for deterministic Brief input."""
    eligible = anchors_for_slide(_valid_anchors(), slide_number=1)
    names = [a["name"] for a in eligible]
    assert names == ["The Customer", "The Sales Rep", "Cocktail Napkin", "Period Palette"]


def test_anchors_for_slide_empty_anchors_returns_empty_list():
    eligible = anchors_for_slide({"schema_version": "1.0.0", "anchors": []}, slide_number=1)
    assert eligible == []


# ---------------------------------------------------------------------------
# format_anchors_for_brief
# ---------------------------------------------------------------------------


def test_format_anchors_for_brief_empty_returns_empty_string():
    """Empty anchors + no deck_brief → empty result (caller can append unconditionally)."""
    assert format_anchors_for_brief([]) == ""
    assert format_anchors_for_brief([], deck_brief=None) == ""


def test_format_anchors_for_brief_with_deck_brief_only():
    """deck_brief without anchors still produces output."""
    out = format_anchors_for_brief([], deck_brief="Wall Street 1980s")
    assert "Recurring entities from creative anchors" in out
    assert "Wall Street 1980s" in out


def test_format_anchors_for_brief_groups_by_kind():
    """The format groups anchors by kind for readability — characters first,
    then props, then locations, then style anchors."""
    eligible = anchors_for_slide(_valid_anchors(), slide_number=1)
    out = format_anchors_for_brief(eligible, deck_brief=_valid_anchors()["deck_brief"])
    # Find the positions of each section header
    char_idx = out.index("characters")
    prop_idx = out.index("props")
    style_idx = out.index("style_anchors")
    assert char_idx < prop_idx < style_idx, (
        "Anchors must be grouped in stable order: characters, props, style_anchors"
    )


def test_format_anchors_for_brief_inlines_descriptions():
    """Every anchor's description must appear verbatim in the output."""
    eligible = anchors_for_slide(_valid_anchors(), slide_number=1)
    out = format_anchors_for_brief(eligible)
    for anchor in eligible:
        assert anchor["description"] in out
        assert anchor["name"] in out


def test_format_anchors_for_brief_inlines_negative_traits():
    """Negative traits must surface as 'Must NOT have:' lines so the Brief
    can express them as exclusions in the prompt."""
    eligible = anchors_for_slide(_valid_anchors(), slide_number=1)
    out = format_anchors_for_brief(eligible)
    assert "Must NOT have: beard" in out


def test_format_anchors_for_brief_closes_with_usage_directive():
    """The section ends with a directive telling the Brief to use these
    descriptions verbatim — without it the Brief might paraphrase."""
    eligible = anchors_for_slide(_valid_anchors(), slide_number=1)
    out = format_anchors_for_brief(eligible)
    assert "use the description above verbatim" in out


# ---------------------------------------------------------------------------
# Brief integration — anchors flow through build_brief_input
# ---------------------------------------------------------------------------


def test_build_brief_input_omits_anchors_section_when_none():
    """When anchors_section is None / empty, the Brief input is unchanged
    from the pre-AC4 shape — existing dispatches that don't pass anchors
    are not broken."""
    blob = build_brief_input(
        vision_prose="A lighthouse at sunset",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="ollama",
        brand_fidelity="none",
    )
    assert "Recurring entities from creative anchors" not in blob
    assert "A lighthouse at sunset" in blob


def test_build_brief_input_inlines_anchors_section_before_prose():
    """When an anchors section is provided, it precedes the prose. This
    ordering matters — the Brief is supposed to read anchors first so
    when it parses the prose it can recognise the anchor names and bind
    them to the canonical descriptions."""
    eligible = anchors_for_slide(_valid_anchors(), slide_number=1)
    section = format_anchors_for_brief(eligible)
    blob = build_brief_input(
        vision_prose="The Customer enters the bar with The Sales Rep",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="ollama",
        brand_fidelity="none",
        anchors_section=section,
    )
    assert "Recurring entities from creative anchors" in blob
    # Anchors section appears BEFORE the prose section
    anchors_idx = blob.index("Recurring entities from creative anchors")
    prose_idx = blob.index("Operator's vision prose")
    assert anchors_idx < prose_idx
    # Anchor descriptions are in the blob the Brief receives
    assert "tortoiseshell glasses" in blob
    assert "salt-and-pepper hair" in blob


def test_build_brief_input_empty_anchors_section_treated_as_none():
    """An empty string as anchors_section should produce the same output as
    None — the formatter returns '' when there's nothing to format, and the
    Brief input shouldn't get an orphan blank line."""
    blob_none = build_brief_input(
        vision_prose="p",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="ollama",
        brand_fidelity="none",
    )
    blob_empty = build_brief_input(
        vision_prose="p",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="ollama",
        brand_fidelity="none",
        anchors_section="",
    )
    assert blob_none == blob_empty
