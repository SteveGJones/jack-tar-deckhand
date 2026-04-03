"""Tests for slide prompt composer."""

import json
import os
import shutil
import tempfile
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
    """Content with many bullets should now classify as 'background'."""
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][1])
    assert result["strategy"] == "background"


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


def test_assemble_brief_full_render(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][0]  # title slide
    brief = assemble_brief(slide, "full_render", sample_style_guide, sample_brand_profile, "ollama")
    assert brief["slide_number"] == 1
    assert brief["strategy"] == "full_render"
    assert brief["headline"] == "Big Title"
    assert "006B5E" in brief["brand_constraints"]["palette_hex"]
    assert "clip art" in brief["brand_constraints"]["prohibited_styles"]
    assert brief["funnel_stage"] == "ollama"
    assert brief["target_resolution"] == "1024x576"


def test_assemble_brief_backdrop_excludes_text(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][1]  # content slide with 4 bullets
    brief = assemble_brief(slide, "backdrop_render", sample_style_guide, sample_brand_profile, "cloud_full")
    assert brief["strategy"] == "backdrop_render"
    assert brief["text_instruction"] == "NO TEXT in the image — leave clean space for text overlay"
    assert brief["target_resolution"] == "1920x1080"


def test_assemble_brief_cloud_low_resolution(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][0]
    brief = assemble_brief(slide, "full_render", sample_style_guide, sample_brand_profile, "cloud_low")
    assert brief["target_resolution"] == "1280x720"


def test_assemble_brief_includes_visual_direction(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][0]
    brief = assemble_brief(slide, "full_render", sample_style_guide, sample_brand_profile, "ollama")
    assert brief["visual_direction"] == "Dramatic hero image"


def test_assemble_brief_includes_style_tokens(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][0]
    brief = assemble_brief(slide, "full_render", sample_style_guide, sample_brand_profile, "ollama")
    assert "Professional, precise" in brief["style_tokens"]["mood"]


@pytest.fixture
def deck_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


def test_save_and_load_strategy_map(deck_dir, sample_outline):
    from src.slide_prompt_composer import build_strategy_map, save_strategy_map, load_strategy_map
    strategy_map = build_strategy_map(sample_outline)
    save_strategy_map(deck_dir, strategy_map)
    loaded = load_strategy_map(deck_dir)
    assert loaded["approval_mode"] == "review"
    assert len(loaded["slides"]) == 6


def test_save_strategy_map_validates_schema(deck_dir):
    from src.slide_prompt_composer import save_strategy_map
    bad_map = {"approval_mode": "invalid", "slides": []}
    with pytest.raises(Exception):
        save_strategy_map(deck_dir, bad_map)


def test_load_strategy_map_missing_file(deck_dir):
    from src.slide_prompt_composer import load_strategy_map
    with pytest.raises(FileNotFoundError):
        load_strategy_map(deck_dir)


def test_strategy_map_accepts_background_strategy(sample_outline):
    """StrategyMap schema should accept 'background' as a valid strategy."""
    from src.slide_prompt_composer import build_strategy_map
    import jsonschema
    result = build_strategy_map(sample_outline)
    result['slides'][1]['strategy'] = 'background'
    result['slides'][1]['backdrop_variant'] = 'bottom_bar'
    with open('src/schemas/strategy_map.schema.json') as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(result)


def test_strategy_map_accepts_backdrop_strategy(sample_outline):
    """StrategyMap schema should accept 'backdrop' with element_layout."""
    from src.slide_prompt_composer import build_strategy_map
    import jsonschema
    result = build_strategy_map(sample_outline)
    result['slides'][1]['strategy'] = 'backdrop'
    result['slides'][1]['element_layout'] = {
        'template': 'three_across',
        'elements': [
            {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.08, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.38, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            {'id': 'elem_3', 'label_source': 'body_points[2]', 'x': 0.67, 'y': 0.25, 'w': 0.25, 'h': 0.50},
        ],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    with open('src/schemas/strategy_map.schema.json') as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(result)


def test_strategy_map_accepts_pragmatic_composition(sample_outline):
    """StrategyMap schema should accept 'pragmatic_composition'."""
    from src.slide_prompt_composer import build_strategy_map
    import jsonschema
    result = build_strategy_map(sample_outline)
    result['slides'][1]['strategy'] = 'pragmatic_composition'
    result['slides'][1]['element_layout'] = {
        'template': 'two_column',
        'elements': [
            {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.20, 'w': 0.40, 'h': 0.60},
            {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.55, 'y': 0.20, 'w': 0.40, 'h': 0.60},
        ],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    with open('src/schemas/strategy_map.schema.json') as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(result)


def test_strategy_map_accepts_backdrop_variant(sample_outline):
    """StrategyMap schema should accept backdrop_variant field."""
    from src.slide_prompt_composer import build_strategy_map
    import jsonschema
    result = build_strategy_map(sample_outline)
    result['slides'][1]['strategy'] = 'background'
    for variant in ['left_panel', 'right_panel', 'bottom_bar', 'top_band', 'center_float']:
        result['slides'][1]['backdrop_variant'] = variant
        with open('src/schemas/strategy_map.schema.json') as f:
            schema = json.load(f)
        jsonschema.Draft202012Validator(schema).validate(result)


def test_classify_content_with_many_bullets_as_background():
    """Content slide with >2 bullets should classify as 'background' (not backdrop_render)."""
    from src.slide_prompt_composer import classify_slide_strategy
    slide = {'slide_number': 2, 'slide_type': 'content',
             'body_points': ['A', 'B', 'C', 'D'], 'visual_type': 'hero_image'}
    result = classify_slide_strategy(slide)
    assert result['strategy'] == 'background'


def test_classify_backdrop_render_still_accepted():
    """Backward compat: existing code producing backdrop_render should still work."""
    from src.slide_prompt_composer import build_strategy_map
    outline = {'slides': [
        {'slide_number': 1, 'slide_type': 'content',
         'body_points': ['A', 'B', 'C'], 'visual_type': 'hero_image'},
    ]}
    overrides = {1: 'backdrop_render'}
    result = build_strategy_map(outline, overrides=overrides)
    assert result['slides'][0]['speaker_override'] == 'backdrop_render'


def test_element_layout_three_across():
    """three_across template should produce 3 evenly-spaced columns."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('three_across', 3)
    assert layout['template'] == 'three_across'
    assert len(layout['elements']) == 3
    assert all(0 <= e['x'] <= 1 and 0 <= e['y'] <= 1 for e in layout['elements'])
    assert 'title_region' in layout
    # Elements should be horizontally spaced
    xs = [e['x'] for e in layout['elements']]
    assert xs[0] < xs[1] < xs[2]


def test_element_layout_two_column():
    """two_column template should produce 2 wide columns."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('two_column', 2)
    assert len(layout['elements']) == 2


def test_element_layout_grid_2x2():
    """grid_2x2 template should produce 4 elements in a 2x2 grid."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('grid_2x2', 4)
    assert len(layout['elements']) == 4


def test_element_layout_process_flow():
    """process_flow template should produce a horizontal row."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('process_flow', 4)
    assert len(layout['elements']) == 4
    xs = [e['x'] for e in layout['elements']]
    assert xs == sorted(xs)


def test_element_layout_hub_and_spoke():
    """hub_and_spoke template should have 1 centre + surrounding elements."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('hub_and_spoke', 4)
    assert len(layout['elements']) == 4


def test_element_layout_caps_at_5():
    """Element count must be capped at 5."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('process_flow', 5)
    assert len(layout['elements']) == 5
    with pytest.raises(ValueError):
        get_element_layout('process_flow', 6)


def test_select_backdrop_variant():
    """select_backdrop_variant should return a valid variant name."""
    from src.slide_prompt_composer import select_backdrop_variant
    variants = ['left_panel', 'right_panel', 'bottom_bar', 'top_band', 'center_float']
    # Should cycle through variants based on position
    for i in range(5):
        result = select_backdrop_variant(i, 10)
        assert result in variants


def test_select_backdrop_variant_avoids_consecutive_duplicates():
    """Consecutive slides should not get the same variant."""
    from src.slide_prompt_composer import select_backdrop_variant
    results = [select_backdrop_variant(i, 10) for i in range(5)]
    for i in range(1, len(results)):
        assert results[i] != results[i - 1]


def test_assemble_brief_background_includes_variant(sample_outline, sample_style_guide, sample_brand_profile):
    """Background brief should include backdrop_variant and text zone hint."""
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline['slides'][1]
    brief = assemble_brief(slide, 'background', sample_style_guide, sample_brand_profile, 'ollama',
                           backdrop_variant='bottom_bar')
    assert brief['strategy'] == 'background'
    assert brief['backdrop_variant'] == 'bottom_bar'
    assert 'text_instruction' in brief
    assert 'NO TEXT' in brief['text_instruction']


def test_assemble_brief_pragmatic_includes_element_layout(sample_outline, sample_style_guide, sample_brand_profile):
    """Pragmatic composition brief should include element_layout."""
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline['slides'][1]
    element_layout = {
        'template': 'three_across',
        'elements': [{'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.1, 'y': 0.2, 'w': 0.25, 'h': 0.5}],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    brief = assemble_brief(slide, 'pragmatic_composition', sample_style_guide, sample_brand_profile, 'ollama',
                           element_layout=element_layout)
    assert brief['strategy'] == 'pragmatic_composition'
    assert brief['element_layout'] == element_layout


def test_assemble_brief_backdrop_includes_element_layout(sample_outline, sample_style_guide, sample_brand_profile):
    """Backdrop brief should include element_layout for spatial intent."""
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline['slides'][1]
    element_layout = {
        'template': 'two_column',
        'elements': [{'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.1, 'y': 0.2, 'w': 0.4, 'h': 0.6}],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    brief = assemble_brief(slide, 'backdrop', sample_style_guide, sample_brand_profile, 'ollama',
                           element_layout=element_layout)
    assert brief['strategy'] == 'backdrop'
    assert brief['element_layout'] == element_layout


def test_split_element_briefs(sample_style_guide, sample_brand_profile):
    """split_element_briefs should produce 1 background + N element briefs."""
    from src.slide_prompt_composer import split_element_briefs, get_element_layout
    slide = {'slide_number': 11, 'slide_type': 'content', 'headline': 'Three Options',
             'body_points': ['Option A', 'Option B', 'Option C'],
             'visual_direction': 'Three panels showing different approaches'}
    layout = get_element_layout('three_across', 3)
    briefs = split_element_briefs(slide, sample_style_guide, sample_brand_profile, layout, 'ollama')
    assert len(briefs) == 4  # 1 bg + 3 elements
    assert briefs[0]['role'] == 'background'
    assert briefs[1]['role'] == 'element'
    assert briefs[1]['element_id'] == 'elem_1'
    # All should share a style prefix
    assert briefs[1]['shared_style_prefix'] == briefs[2]['shared_style_prefix']


def test_split_element_briefs_no_text_instruction(sample_style_guide, sample_brand_profile):
    """All element briefs should include NO TEXT instruction."""
    from src.slide_prompt_composer import split_element_briefs, get_element_layout
    slide = {'slide_number': 11, 'slide_type': 'content', 'headline': 'Test',
             'body_points': ['A', 'B'], 'visual_direction': 'Two panels'}
    layout = get_element_layout('two_column', 2)
    briefs = split_element_briefs(slide, sample_style_guide, sample_brand_profile, layout, 'ollama')
    for brief in briefs:
        assert 'NO TEXT' in brief['text_instruction']


def test_classify_does_not_produce_smartart_strategy():
    """classify_slide_strategy should never produce 'smartart' — that comes from the selector."""
    from src.slide_prompt_composer import classify_slide_strategy
    # Try a slide that might tempt smartart classification (content with visual_intent)
    slide = {
        'slide_number': 5,
        'slide_type': 'content',
        'headline': 'Our Process',
        'body_points': ['Research', 'Design', 'Build', 'Launch'],
        'visual_direction': 'Show as a flowchart'
    }
    result = classify_slide_strategy(slide)
    # classify_slide_strategy can only return: composed, full_render, or background
    # Never smartart — that comes from the SmartArt selector skill
    assert result['strategy'] != 'smartart'
    assert result['strategy'] in ['composed', 'full_render', 'background']
