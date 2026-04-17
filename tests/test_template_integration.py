"""Integration tests for template-driven layout pipeline."""

import json
import os
import pytest

from src.slide_prompt_composer import classify_slide_strategy, build_strategy_map


class TestTemplateStrategyConstraints:
    def test_template_mode_forces_composed(self):
        slide = {'slide_number': 1, 'slide_type': 'content', 'headline': 'Test',
                 'body_points': ['A'], 'visual_type': 'hero_image'}
        result = classify_slide_strategy(slide, template_mode=True)
        assert result['strategy'] == 'composed'

    def test_template_mode_title_stays_composed(self):
        slide = {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title',
                 'visual_type': 'hero_image'}
        result = classify_slide_strategy(slide, template_mode=True)
        assert result['strategy'] == 'composed'

    def test_template_mode_full_bleed_picture_allows_full_render(self):
        slide = {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title',
                 'visual_type': 'hero_image'}
        full_bleed_layout = {
            'placeholders': [
                {'idx': 13, 'type': 'picture', 'name': 'Picture', 'x': 0.0, 'y': 0.0, 'w': 13.33, 'h': 7.5},
            ]
        }
        result = classify_slide_strategy(slide, template_mode=True, template_layout=full_bleed_layout)
        assert result['strategy'] == 'full_render'

    def test_template_mode_small_picture_stays_composed(self):
        slide = {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title',
                 'visual_type': 'hero_image'}
        small_pic_layout = {
            'placeholders': [
                {'idx': 13, 'type': 'picture', 'name': 'Picture', 'x': 7.0, 'y': 0.0, 'w': 6.0, 'h': 7.5},
            ]
        }
        result = classify_slide_strategy(slide, template_mode=True, template_layout=small_pic_layout)
        assert result['strategy'] == 'composed'

    def test_without_template_mode_unchanged(self):
        slide = {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title',
                 'visual_type': 'hero_image'}
        result = classify_slide_strategy(slide, template_mode=False)
        assert result['strategy'] == 'full_render'

    def test_build_strategy_map_template_mode(self):
        outline = {
            'narrative_arc': 'test',
            'estimated_duration_minutes': 10,
            'slides': [
                {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title', 'visual_type': 'hero_image'},
                {'slide_number': 2, 'slide_type': 'content', 'headline': 'Content',
                 'body_points': ['A', 'B', 'C', 'D'], 'visual_type': 'hero_image'},
            ],
        }
        strategy_map = build_strategy_map(outline, template_mode=True)
        for entry in strategy_map['slides']:
            assert entry['strategy'] == 'composed'

    def test_build_strategy_map_render_funnel_ollama_only(self):
        outline = {
            'narrative_arc': 'test',
            'estimated_duration_minutes': 10,
            'slides': [
                {'slide_number': 1, 'slide_type': 'content', 'headline': 'Test', 'visual_type': 'hero_image'},
            ],
        }
        strategy_map = build_strategy_map(outline, template_mode=True)
        assert strategy_map['slides'][0]['render_funnel'] == ['ollama']


from src.deckcontext import DEFAULT_STEP_ORDER


class TestPipelineStepOrder:
    def test_template_analysis_in_step_order(self):
        assert 'template-analysis' in DEFAULT_STEP_ORDER

    def test_template_analysis_before_brand_manager(self):
        ta_idx = DEFAULT_STEP_ORDER.index('template-analysis')
        bm_idx = DEFAULT_STEP_ORDER.index('brand-manager')
        assert ta_idx < bm_idx

    def test_template_analysis_after_validate_brief(self):
        ta_idx = DEFAULT_STEP_ORDER.index('template-analysis')
        vb_idx = DEFAULT_STEP_ORDER.index('validate-brief')
        assert ta_idx > vb_idx
