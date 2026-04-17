"""Tests for template analyser and template profile schema."""

import json
import os
import pytest
import jsonschema

from src.deckcontext import read_contract, write_contract


SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')


def _load_schema():
    with open(os.path.join(SCHEMA_DIR, 'template_profile.schema.json')) as f:
        return json.load(f)


def _minimal_profile():
    return {
        'template_path': '/tmp/template.pptx',
        'template_hash': 'a' * 64,
        'slide_width_inches': 13.333,
        'slide_height_inches': 7.5,
        'master_index': 0,
        'layouts': [
            {
                'name': 'Content 1',
                'index': 0,
                'placeholder_count': 2,
                'placeholders': [
                    {'idx': 0, 'type': 'title', 'name': 'Title 1', 'x': 0.6, 'y': 0.6, 'w': 12.13, 'h': 1.02},
                    {'idx': 31, 'type': 'content', 'name': 'Content Placeholder 5', 'x': 0.6, 'y': 2.33, 'w': 12.13, 'h': 4.57},
                ],
                'decorative_shape_count': 0,
            }
        ],
        'layout_mapping': {
            'content': {'layout_name': 'Content 1', 'layout_index': 0},
        },
        'unmapped_fallback': {'layout_name': 'Content 1', 'layout_index': 0},
        'constrains_strategies': True,
        'speaker_approved': False,
    }


class TestTemplateProfileSchema:
    def test_valid_profile_passes(self):
        schema = _load_schema()
        jsonschema.validate(instance=_minimal_profile(), schema=schema)

    def test_missing_required_field_fails(self):
        schema = _load_schema()
        profile = _minimal_profile()
        del profile['template_hash']
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=profile, schema=schema)

    def test_invalid_hash_pattern_fails(self):
        schema = _load_schema()
        profile = _minimal_profile()
        profile['template_hash'] = 'not-a-hash'
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=profile, schema=schema)

    def test_invalid_placeholder_type_fails(self):
        schema = _load_schema()
        profile = _minimal_profile()
        profile['layouts'][0]['placeholders'][0]['type'] = 'invalid_type'
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=profile, schema=schema)

    def test_write_and_read_via_deckcontext(self, tmp_path):
        profile = _minimal_profile()
        deck_dir = str(tmp_path)
        write_contract(deck_dir, 'template-profile', profile)
        loaded = read_contract(deck_dir, 'template-profile')
        assert loaded['template_hash'] == 'a' * 64
        assert loaded['layouts'][0]['name'] == 'Content 1'
