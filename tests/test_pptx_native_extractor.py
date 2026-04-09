"""Tests for pptx_native support in src.smartart_extractor."""
from __future__ import annotations

import pytest


STYLE_GUIDE = {
    "palette": {
        "primary": "1a73e8",
        "accent": "e8710a",
        "background": "ffffff",
        "text_primary": "1a1a1a",
        "chart_series": ["2B6CB0", "ED8936", "38A169", "E53E3E"],
    },
    "typography": {"heading_font": "Inter", "body_font": "Inter"},
}


def test_extract_flowchart_with_pptx_native_engine():
    """flowchart + engine=pptx_native produces a spec with {'steps': [...]}."""
    from src.smartart_extractor import extract

    slide = {
        "slide_number": 4,
        "headline": "Our Process",
        "body_points": ["Research", "Design", "Build", "Test", "Ship"],
    }
    selection = {
        "slide_number": 4,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    assert spec["engine"] == "pptx_native"
    assert spec["graphic_type"] == "flowchart"
    assert spec["validation_status"] == "valid"
    assert spec["data"] == {
        "items": ["Research", "Design", "Build", "Test", "Ship"]
    }


def test_extract_pptx_native_preserves_slide_number():
    from src.smartart_extractor import extract

    spec = extract(
        {"slide_number": 12, "body_points": ["A", "B", "C"]},
        {
            "slide_number": 12,
            "graphic_type": "flowchart",
            "enrichment_tier": "pure_programmatic",
            "engine": "pptx_native",
        },
        STYLE_GUIDE,
    )
    assert spec["slide_number"] == 12


def test_extract_pptx_native_strips_whitespace_and_unsafe_chars():
    """_clean_label strips leading/trailing whitespace and Mermaid-breaking
    characters (quotes, brackets, braces, pipes). It does NOT strip numeric
    prefixes — speaker-written numbering is preserved verbatim because
    PowerPoint's Basic Process doesn't auto-number."""
    from src.smartart_extractor import extract

    slide = {
        "slide_number": 1,
        "body_points": [
            "  Research   ",       # extra whitespace
            "Design [draft]",      # brackets
            'Build "v1"',          # quotes
        ],
    }
    selection = {
        "slide_number": 1,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    steps = spec["data"]["items"]
    assert steps[0] == "Research"
    assert "[" not in steps[1] and "]" not in steps[1]
    assert '"' not in steps[2]
    for step in steps:
        assert step.strip() == step  # no leading/trailing whitespace


def test_extract_pptx_native_preserves_speaker_numbering():
    """Numeric prefixes stay as-is — the speaker chose to write them."""
    from src.smartart_extractor import extract

    slide = {"slide_number": 1, "body_points": ["1. Plan", "2. Execute", "3. Review"]}
    selection = {
        "slide_number": 1,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    assert spec["data"]["items"] == ["1. Plan", "2. Execute", "3. Review"]


def test_extract_pptx_native_passthrough_inline_data():
    """When slide.data.inline_data is present, it passes through as-is."""
    from src.smartart_extractor import extract

    slide = {
        "slide_number": 1,
        "body_points": ["ignored"],
        "data": {"inline_data": {"items": ["Explicit", "Steps"]}},
    }
    selection = {
        "slide_number": 1,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    assert spec["data"] == {"items": ["Explicit", "Steps"]}


def test_extract_pptx_native_produces_spec_accepted_by_engine():
    """End-to-end: extractor output → renderer → valid manifest entry."""
    import tempfile
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        "slide_number": 9,
        "headline": "Phased Rollout",
        "body_points": ["Plan", "Build", "Test", "Ship"],
    }
    selection = {
        "slide_number": 9,
        "graphic_type": "flowchart",
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, STYLE_GUIDE, "production", tmpdir)
        assert entry["status"] == "rendered"
        assert entry["engine_used"] == "pptx_native"
        assert entry["slide_number"] == 9


def test_extract_validate_spec_knows_pptx_native():
    """validate_spec should accept pptx_native as a valid engine."""
    from src.smartart_extractor import validate_spec

    valid, errors = validate_spec({
        "engine": "pptx_native",
        "graphic_type": "flowchart",
        "data": {"items": ["A", "B"]},
    })
    assert valid is True
    assert errors == []


def test_extract_pptx_native_with_unsupported_graphic_type_falls_through():
    """Unsupported graphic_type produces an items fallback (layout
    builder will reject at render time — that's the safety net)."""
    from src.smartart_extractor import extract

    slide = {"slide_number": 1, "body_points": ["A", "B", "C"]}
    selection = {
        "slide_number": 1,
        "graphic_type": "swot",  # no pptx_native mapping in v1
        "enrichment_tier": "pure_programmatic",
        "engine": "pptx_native",
    }
    spec = extract(slide, selection, STYLE_GUIDE)
    # The extractor emits a fallback shape; the renderer would fail
    # when the layout-lookup-by-graphic-type returns None.
    assert spec["engine"] == "pptx_native"
    assert "items" in spec["data"]
