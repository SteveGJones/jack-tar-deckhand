"""Tests for image routing logic — routing matrix, fallback chains, classification."""

import json
import os
import pytest
from src.image_router import plan_production_upgrade, UpgradeDecision, load_upgrade_plan, execute_upgrade_plan_entry

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


# --- Provider availability scenarios ---

ALL_PROVIDERS = {
    'ollama': {'available': True, 'models': ['x/z-image-turbo', 'x/flux2-klein']},
    'openai': {'available': True, 'model': 'gpt-image-1.5'},
    'google': {'available': True, 'model': 'imagen-4'},
    'fal': {'available': True, 'models': ['flux-2-pro', 'recraft-v4']},
    'recraft': {'available': True, 'model': 'recraft-v4'},
}

OLLAMA_ONLY = {
    'ollama': {'available': True, 'models': ['x/z-image-turbo', 'x/flux2-klein']},
    'openai': {'available': False},
    'google': {'available': False},
    'fal': {'available': False},
    'recraft': {'available': False},
}

CLOUD_ONLY = {
    'ollama': {'available': False, 'models': []},
    'openai': {'available': True, 'model': 'gpt-image-1.5'},
    'google': {'available': True, 'model': 'imagen-4'},
    'fal': {'available': True, 'models': ['flux-2-pro', 'recraft-v4']},
    'recraft': {'available': True, 'model': 'recraft-v4'},
}

NO_PROVIDERS = {
    'ollama': {'available': False, 'models': []},
    'openai': {'available': False},
    'google': {'available': False},
    'fal': {'available': False},
    'recraft': {'available': False},
}


class TestClassifyVisualType:
    def test_explicit_visual_type_returned(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 1, 'slide_type': 'title', 'visual_type': 'hero_image'}
        assert classify_visual_type(slide) == 'hero_image'

    def test_none_visual_type(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 9, 'slide_type': 'content', 'visual_type': 'none'}
        assert classify_visual_type(slide) == 'none'

    def test_chart_visual_type(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 5, 'slide_type': 'data_chart', 'visual_type': 'chart'}
        assert classify_visual_type(slide) == 'chart'

    def test_missing_visual_type_infers_from_slide_type(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 1, 'slide_type': 'title'}
        assert classify_visual_type(slide) == 'hero_image'

    def test_data_chart_slide_type_infers_chart(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 5, 'slide_type': 'data_chart'}
        assert classify_visual_type(slide) == 'chart'

    def test_closing_slide_type_infers_none(self):
        from src.image_router import classify_visual_type
        slide = {'slide_number': 10, 'slide_type': 'closing'}
        assert classify_visual_type(slide) == 'none'


class TestRouteSlideDraftMode:
    def test_hero_image_routes_to_ollama_image(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'ollama-image'

    def test_icon_set_routes_to_cloud_icon(self):
        from src.image_router import route_slide
        slide = {'slide_number': 3, 'visual_type': 'icon_set'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'cloud-generate-icon'

    def test_pattern_routes_to_ollama_pattern(self):
        from src.image_router import route_slide
        slide = {'slide_number': 2, 'visual_type': 'pattern_background'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'ollama-pattern'

    def test_diagram_routes_to_ollama_diagram(self):
        from src.image_router import route_slide
        slide = {'slide_number': 6, 'visual_type': 'diagram'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'ollama-diagram'

    def test_chart_routes_to_render_chart(self):
        from src.image_router import route_slide
        slide = {'slide_number': 5, 'visual_type': 'chart'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'render_chart'

    def test_none_routes_to_skip(self):
        from src.image_router import route_slide
        slide = {'slide_number': 9, 'visual_type': 'none'}
        decision = route_slide(slide, 'draft', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'skip'


class TestRouteSlideProductionMode:
    def test_hero_image_routes_to_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'cloud-generate-image'

    def test_pattern_routes_to_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 2, 'visual_type': 'pattern_background'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'cloud-generate-image'

    def test_icon_still_routes_to_cloud_icon(self):
        from src.image_router import route_slide
        slide = {'slide_number': 3, 'visual_type': 'icon_set'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'cloud-generate-icon'

    def test_diagram_still_routes_to_ollama_diagram(self):
        from src.image_router import route_slide
        slide = {'slide_number': 6, 'visual_type': 'diagram'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'ollama-diagram'

    def test_chart_still_routes_to_render_chart(self):
        from src.image_router import route_slide
        slide = {'slide_number': 5, 'visual_type': 'chart'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow')
        assert decision.skill == 'render_chart'


class TestFallbackChains:
    def test_hero_falls_back_to_ollama_when_no_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', OLLAMA_ONLY, 'allow')
        assert decision.skill == 'ollama-image'
        assert decision.is_fallback is True

    def test_hero_falls_back_to_placeholder_when_no_providers(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', NO_PROVIDERS, 'allow')
        assert decision.skill == 'placeholder'

    def test_icon_falls_back_to_placeholder_when_no_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 3, 'visual_type': 'icon_set'}
        decision = route_slide(slide, 'draft', OLLAMA_ONLY, 'allow')
        assert decision.skill == 'placeholder'
        assert decision.is_fallback is True

    def test_pattern_falls_back_to_ollama_when_no_cloud(self):
        from src.image_router import route_slide
        slide = {'slide_number': 2, 'visual_type': 'pattern_background'}
        decision = route_slide(slide, 'production', OLLAMA_ONLY, 'allow')
        assert decision.skill == 'ollama-pattern'
        assert decision.is_fallback is True

    def test_diagram_succeeds_with_ollama_only(self):
        from src.image_router import route_slide
        slide = {'slide_number': 6, 'visual_type': 'diagram'}
        decision = route_slide(slide, 'draft', OLLAMA_ONLY, 'allow')
        assert decision.skill == 'ollama-diagram'
        assert decision.is_fallback is False

    def test_chart_succeeds_with_no_providers(self):
        from src.image_router import route_slide
        slide = {'slide_number': 5, 'visual_type': 'chart'}
        decision = route_slide(slide, 'draft', NO_PROVIDERS, 'allow')
        assert decision.skill == 'render_chart'
        assert decision.is_fallback is False


class TestBudgetDegradation:
    def test_degrade_forces_ollama_for_hero(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'degrade')
        assert decision.skill == 'ollama-image'

    def test_degrade_forces_placeholder_for_icons_when_no_ollama(self):
        from src.image_router import route_slide
        slide = {'slide_number': 3, 'visual_type': 'icon_set'}
        decision = route_slide(slide, 'production', CLOUD_ONLY, 'degrade')
        assert decision.skill == 'placeholder'

    def test_typography_only_forces_placeholder(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'typography_only')
        assert decision.skill == 'placeholder'

    def test_typography_only_still_allows_charts(self):
        from src.image_router import route_slide
        slide = {'slide_number': 5, 'visual_type': 'chart'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'typography_only')
        assert decision.skill == 'render_chart'

    def test_allow_with_caps_downgrades_hero_model(self):
        from src.image_router import route_slide
        slide = {'slide_number': 1, 'visual_type': 'hero_image'}
        decision = route_slide(slide, 'production', ALL_PROVIDERS, 'allow_with_caps')
        assert decision.skill == 'cloud-generate-image'
        assert decision.model == 'imagen-4-fast'


class TestRouteAllSlides:
    def test_routes_all_slides_in_fixture(self):
        from src.image_router import route_all_slides
        outline = load_fixture('routing_slide_outline')
        decisions = route_all_slides(outline, 'draft', ALL_PROVIDERS, 'allow')
        # Charts excluded from route_all_slides, none slides included as skip
        # hero(1) + pattern(2) + icon(3) + hero(4) + diagram(6) + pattern(7) + icon(8) + none(9) + none(10) = 9
        image_decisions = [d for d in decisions if d.skill != 'skip']
        assert len(image_decisions) == 7

    def test_all_placeholders_when_no_providers(self):
        from src.image_router import route_all_slides
        outline = load_fixture('routing_slide_outline')
        decisions = route_all_slides(outline, 'draft', NO_PROVIDERS, 'allow')
        image_decisions = [d for d in decisions if d.skill != 'skip']
        for d in image_decisions:
            assert d.skill == 'placeholder'


class TestGetChartSlides:
    def test_extracts_chart_slides(self):
        from src.image_router import get_chart_slides
        outline = load_fixture('routing_slide_outline')
        charts = get_chart_slides(outline)
        assert len(charts) == 1
        assert charts[0]['slide_number'] == 5
        assert charts[0]['data']['chart_type'] == 'bar'

    def test_empty_when_no_charts(self):
        from src.image_router import get_chart_slides
        outline = {
            'narrative_arc': 'test',
            'estimated_duration_minutes': 10,
            'slides': [
                {'slide_number': 1, 'slide_type': 'title', 'visual_type': 'hero_image', 'headline': 'Test'}
            ]
        }
        charts = get_chart_slides(outline)
        assert len(charts) == 0


class TestPlaceholderColor:
    def test_hero_uses_background_alt(self):
        from src.image_router import generate_placeholder_color
        palette = {'primary': '1A365D', 'background_alt': '1A202C'}
        assert generate_placeholder_color(palette, 'hero_image') == '1A202C'

    def test_pattern_uses_primary(self):
        from src.image_router import generate_placeholder_color
        palette = {'primary': '1A365D', 'background_alt': '1A202C'}
        assert generate_placeholder_color(palette, 'pattern_background') == '1A365D'

    def test_icon_uses_secondary_or_primary(self):
        from src.image_router import generate_placeholder_color
        palette = {'primary': '1A365D', 'secondary': '2B6CB0', 'background_alt': '1A202C'}
        colour = generate_placeholder_color(palette, 'icon_set')
        assert colour in ('1A365D', '2B6CB0')


@pytest.fixture
def draft_manifest():
    return {
        'images': [
            {
                'image_id': 'slide-01-hero_image',
                'slide_number': 1,
                'file_path': '/tmp/deck/images/slide-01-hero.png',
                'status': 'generated',
                'model_used': 'x/z-image-turbo',
                'source_prompt': 'Dramatic teal composition',
                'dimensions': {'width': 1024, 'height': 576},
            },
            {
                'image_id': 'slide-04-diagram',
                'slide_number': 4,
                'file_path': '/tmp/deck/images/slide-04-diagram.png',
                'status': 'generated',
                'model_used': 'svg-convert',
                'dimensions': {'width': 1705, 'height': 1536},
            },
            {
                'image_id': 'slide-05-hero_image',
                'slide_number': 5,
                'file_path': '/tmp/deck/images/slide-05-hero.png',
                'status': 'generated',
                'model_used': 'x/z-image-turbo',
                'source_prompt': 'Abstract collaboration',
                'dimensions': {'width': 1024, 'height': 576},
            },
        ],
    }


@pytest.fixture
def upgrade_outline():
    return {
        'slides': [
            {'slide_number': 1, 'visual_type': 'hero_image'},
            {'slide_number': 4, 'visual_type': 'diagram'},
            {'slide_number': 5, 'visual_type': 'hero_image'},
        ],
    }


@pytest.fixture
def all_providers():
    return {
        'ollama': {'available': True, 'models': ['x/z-image-turbo']},
        'openai': {'available': True, 'model': 'gpt-image-1.5'},
        'google': {'available': True, 'model': 'imagen-4'},
        'fal': {'available': True, 'models': ['flux-2-pro']},
    }


@pytest.fixture
def budget_allow():
    return {'budget_state': 'allow', 'remaining_usd': 5.0}


def test_plan_upgrade_upgrades_hero_images(draft_manifest, upgrade_outline, all_providers, budget_allow):
    decisions = plan_production_upgrade(draft_manifest, upgrade_outline, all_providers, budget_allow)
    heroes = [d for d in decisions if d.action == 'upgrade']
    assert len(heroes) == 2
    assert heroes[0].slide_number == 1
    assert heroes[1].slide_number == 5


def test_plan_upgrade_keeps_svg_diagrams(draft_manifest, upgrade_outline, all_providers, budget_allow):
    decisions = plan_production_upgrade(draft_manifest, upgrade_outline, all_providers, budget_allow)
    kept = [d for d in decisions if d.action == 'keep']
    assert len(kept) == 1
    assert kept[0].slide_number == 4
    assert 'already' in kept[0].reason.lower()


def test_plan_upgrade_respects_budget(draft_manifest, upgrade_outline, all_providers):
    tight_budget = {'budget_state': 'allow', 'remaining_usd': 0.02}
    decisions = plan_production_upgrade(draft_manifest, upgrade_outline, all_providers, tight_budget)
    upgrades = [d for d in decisions if d.action == 'upgrade']
    total_cost = sum(d.estimated_cost_usd for d in upgrades)
    assert total_cost <= 0.02


def test_plan_upgrade_carries_source_prompt(draft_manifest, upgrade_outline, all_providers, budget_allow):
    decisions = plan_production_upgrade(draft_manifest, upgrade_outline, all_providers, budget_allow)
    slide_1 = [d for d in decisions if d.slide_number == 1][0]
    assert slide_1.draft_prompt == 'Dramatic teal composition'


def test_plan_upgrade_returns_upgrade_decisions(draft_manifest, upgrade_outline, all_providers, budget_allow):
    decisions = plan_production_upgrade(draft_manifest, upgrade_outline, all_providers, budget_allow)
    assert all(isinstance(d, UpgradeDecision) for d in decisions)
    assert len(decisions) == 3


def test_load_upgrade_plan_reads_file(tmp_path):
    plan = {
        'created_at': '2026-03-31T12:00:00Z',
        'deck_dir': str(tmp_path),
        'total_estimated_cost_usd': 0.11,
        'entries': [
            {
                'slide_number': 1,
                'image_id': 'slide-01-hero',
                'upgrade_track': 'raster_upscale',
                'recommended_provider': 'fal',
                'recommended_model': 'flux-2-pro',
                'recommended_tier': 'standard',
                'target_dimensions': '1920x1080',
                'estimated_cost_usd': 0.03,
                'reasoning': 'Abstract hero',
                'brand_notes': None,
                'warnings': [],
                'draft_prompt': 'A dramatic wave',
            },
        ],
    }
    plan_path = tmp_path / 'production-upgrade-plan.json'
    import json
    plan_path.write_text(json.dumps(plan))
    loaded = load_upgrade_plan(str(tmp_path))
    assert len(loaded['entries']) == 1
    assert loaded['entries'][0]['upgrade_track'] == 'raster_upscale'


def test_load_upgrade_plan_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_upgrade_plan(str(tmp_path))


def test_execute_entry_raster_returns_skill_and_provider():
    entry = {
        'upgrade_track': 'raster_upscale',
        'recommended_provider': 'google',
        'recommended_model': 'gemini-3.1-flash-image-preview',
        'recommended_tier': 'flash',
        'target_dimensions': '1920x1080',
    }
    result = execute_upgrade_plan_entry(entry)
    assert result['skill'] == 'cloud-generate-image'
    assert result['provider'] == 'google'
    assert result['model'] == 'gemini-3.1-flash-image-preview'
    assert result['width'] == 1920
    assert result['height'] == 1080


def test_execute_entry_vector_returns_icon_skill():
    entry = {
        'upgrade_track': 'vector_conversion',
        'recommended_provider': 'recraft',
        'recommended_model': 'recraft-v4-svg',
        'recommended_tier': 'standard',
        'target_dimensions': None,
    }
    result = execute_upgrade_plan_entry(entry)
    assert result['skill'] == 'cloud-generate-icon'
    assert result['provider'] == 'recraft'
    assert result['model'] == 'recraft-v4-svg'
    assert result['width'] is None
    assert result['height'] is None


def test_execute_entry_no_upgrade_returns_skip():
    entry = {
        'upgrade_track': 'no_upgrade',
        'recommended_provider': 'local',
        'recommended_model': 'matplotlib',
        'recommended_tier': 'standard',
        'target_dimensions': None,
    }
    result = execute_upgrade_plan_entry(entry)
    assert result['skill'] == 'skip'
