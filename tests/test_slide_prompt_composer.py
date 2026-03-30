"""Tests for slide prompt composer."""

import json
import os
import pytest


@pytest.fixture
def sample_outline():
    return {
        "narrative_arc": "Problem-Demo-Impact",
        "estimated_duration_minutes": 11,
        "slides": [
            {"slide_number": 1, "slide_type": "title", "headline": "Big Title",
             "body_points": ["Speaker Name"], "visual_type": "hero_image",
             "visual_direction": "Dramatic hero image"},
            {"slide_number": 2, "slide_type": "content", "headline": "Problem",
             "body_points": ["Point 1", "Point 2", "Point 3", "Point 4"],
             "visual_type": "hero_image",
             "visual_direction": "Abstract fragmentation"},
            {"slide_number": 3, "slide_type": "section_divider", "headline": "Pivot",
             "body_points": [], "visual_type": "none"},
            {"slide_number": 4, "slide_type": "diagram", "headline": "Architecture",
             "body_points": ["Service A", "Service B", "Service C", "Service D"],
             "visual_type": "diagram",
             "visual_direction": "Technical architecture diagram"},
            {"slide_number": 5, "slide_type": "data_chart", "headline": "Results",
             "body_points": [], "visual_type": "chart"},
            {"slide_number": 6, "slide_type": "closing", "headline": "Thank You",
             "body_points": ["url", "handle"], "visual_type": "none"},
        ],
    }


@pytest.fixture
def sample_style_guide():
    return {
        "palette": {
            "primary": "006B5E",
            "secondary": "4B635B",
            "accent": "5CDBC0",
            "background": "F5FBF7",
            "text_primary": "171D1B",
        },
        "typography": {
            "heading_font": "Inter",
            "body_font": "Inter",
        },
        "image_style_tokens": {
            "mood": "Professional, precise",
            "style_modifiers": ["clean flat illustration"],
        },
    }


@pytest.fixture
def sample_brand_profile():
    return {
        "brand_id": "metamirror",
        "palette": {"primary": "006B5E"},
        "approved_image_styles": ["geometric", "clean flat"],
        "prohibited_image_styles": ["clip art", "stock photo"],
    }


def test_classify_title_as_full_render(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][0])
    assert result["strategy"] == "full_render"


def test_classify_content_with_many_bullets_as_backdrop(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][1])
    assert result["strategy"] == "backdrop_render"


def test_classify_section_divider_as_full_render(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][2])
    assert result["strategy"] == "full_render"


def test_classify_diagram_as_composed(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][3])
    assert result["strategy"] == "composed"


def test_classify_data_chart_as_composed(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][4])
    assert result["strategy"] == "composed"


def test_classify_closing_as_full_render(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][5])
    assert result["strategy"] == "full_render"


def test_classify_returns_rationale(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][0])
    assert "rationale" in result
    assert len(result["rationale"]) > 10


def test_classify_returns_render_funnel(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][0])
    assert "render_funnel" in result
    assert result["render_funnel"] == ["ollama", "cloud_low", "cloud_full"]


def test_build_strategy_map(sample_outline):
    from src.slide_prompt_composer import build_strategy_map
    result = build_strategy_map(sample_outline)
    assert result["approval_mode"] == "review"
    assert len(result["slides"]) == 6
    assert "created_at" in result


def test_build_strategy_map_validates_against_schema(sample_outline):
    import jsonschema
    from src.slide_prompt_composer import build_strategy_map
    result = build_strategy_map(sample_outline)
    with open("src/schemas/strategy_map.schema.json") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(result)


def test_build_strategy_map_with_override(sample_outline):
    from src.slide_prompt_composer import build_strategy_map
    overrides = {4: "full_render"}  # Force diagram slide to full_render
    result = build_strategy_map(sample_outline, overrides=overrides)
    slide_4 = [s for s in result["slides"] if s["slide_number"] == 4][0]
    assert slide_4["speaker_override"] == "full_render"


def test_build_strategy_map_one_shot_mode(sample_outline):
    from src.slide_prompt_composer import build_strategy_map
    result = build_strategy_map(sample_outline, approval_mode="one_shot")
    assert result["approval_mode"] == "one_shot"
