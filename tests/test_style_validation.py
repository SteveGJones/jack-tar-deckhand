"""Tests for StyleGuide validation utilities."""

import json
import os
import pytest

from src.style_validation import (
    validate_style_guide,
    check_palette_contrast,
    check_completeness,
    check_brand_compliance,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _load_fixture(name):
    with open(os.path.join(FIXTURE_DIR, name)) as f:
        return json.load(f)


class TestValidateStyleGuide:
    def test_valid_style_guide_passes(self):
        sg = _load_fixture('valid_style_guide.json')
        errors = validate_style_guide(sg)
        assert len(errors) == 0

    def test_missing_palette_fails(self):
        sg = {"typography": {"heading_font": "Inter", "body_font": "Inter"}, "layout": {}}
        errors = validate_style_guide(sg)
        assert len(errors) > 0


class TestPaletteContrast:
    def test_high_contrast_passes(self):
        palette = {
            'text_primary': '1A202C',
            'background': 'FFFFFF',
            'text_on_dark': 'F7FAFC',
            'background_alt': '1A202C',
            'text_muted': '4A5568',
        }
        issues = check_palette_contrast(palette)
        assert len(issues) == 0

    def test_low_contrast_fails(self):
        palette = {
            'text_primary': 'CCCCCC',
            'background': 'DDDDDD',
            'text_on_dark': '333333',
            'background_alt': '222222',
            'text_muted': 'EEEEEE',
        }
        issues = check_palette_contrast(palette)
        assert len(issues) > 0

    def test_returns_specific_failing_pairs(self):
        palette = {
            'text_primary': 'CCCCCC',
            'background': 'DDDDDD',
            'text_on_dark': 'F7FAFC',
            'background_alt': '1A202C',
            'text_muted': '718096',
        }
        issues = check_palette_contrast(palette)
        assert any('text_primary' in i for i in issues)


class TestCompleteness:
    def test_all_layout_templates_present(self):
        sg = _load_fixture('valid_style_guide.json')
        sg['layout']['templates'] = {
            'title': {}, 'section_divider': {}, 'content': {},
            'two_column': {}, 'image_feature': {}, 'data_chart': {},
            'stat_callout': {}, 'quote': {}, 'icon_grid': {},
            'diagram': {}, 'closing': {}, 'blank_visual': {},
        }
        issues = check_completeness(sg)
        template_issues = [i for i in issues if 'template' in i.lower()]
        assert len(template_issues) == 0

    def test_missing_templates_reported(self):
        sg = _load_fixture('valid_style_guide.json')
        sg['layout']['templates'] = {'content': {}}
        issues = check_completeness(sg)
        assert len(issues) > 0


class TestBrandCompliance:
    def test_strict_mode_passes_when_values_match(self):
        brand = _load_fixture('valid_brand_profile.json')
        brand['compliance_mode'] = 'strict'
        sg = _load_fixture('valid_style_guide.json')
        sg['palette']['primary'] = brand['palette']['primary']
        sg['palette']['secondary'] = brand['palette']['secondary']
        sg['typography']['heading_font'] = brand['typography']['heading_font']
        sg['typography']['body_font'] = brand['typography']['body_font']
        issues = check_brand_compliance(sg, brand)
        assert len(issues) == 0

    def test_strict_mode_fails_when_primary_differs(self):
        brand = _load_fixture('valid_brand_profile.json')
        brand['compliance_mode'] = 'strict'
        sg = _load_fixture('valid_style_guide.json')
        sg['palette']['primary'] = 'FF0000'
        issues = check_brand_compliance(sg, brand)
        assert any('primary' in i for i in issues)

    def test_guided_mode_always_passes(self):
        brand = _load_fixture('valid_brand_profile.json')
        brand['compliance_mode'] = 'guided'
        sg = _load_fixture('valid_style_guide.json')
        sg['palette']['primary'] = 'FF0000'
        issues = check_brand_compliance(sg, brand)
        assert len(issues) == 0
