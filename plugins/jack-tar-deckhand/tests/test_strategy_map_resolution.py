"""StrategyMap schema must accept optional per-slide resolution and the
new cloud_2k/cloud_4k funnel stages."""
import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / 'src' / 'schemas' / 'strategy_map.schema.json'
)


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def _base_slide():
    return {
        'slide_number': 1,
        'strategy': 'full_render',
        'rationale': 'hero opener',
        'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
    }


def test_4k_resolution_allowed(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'resolution': '4K'}],
    }
    jsonschema.validate(sm, schema)  # should not raise


def test_2k_resolution_allowed(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'resolution': '2K'}],
    }
    jsonschema.validate(sm, schema)


def test_1k_resolution_allowed(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'resolution': '1K'}],
    }
    jsonschema.validate(sm, schema)


def test_512_resolution_allowed(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'resolution': '512'}],
    }
    jsonschema.validate(sm, schema)


def test_invalid_resolution_rejected(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'resolution': '8K'}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(sm, schema)


def test_render_funnel_accepts_cloud_2k_and_cloud_4k(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{
            **_base_slide(),
            'render_funnel': ['ollama', 'cloud_low', 'cloud_full', 'cloud_2k', 'cloud_4k'],
            'resolution': '4K',
        }],
    }
    jsonschema.validate(sm, schema)


def test_resolution_omitted_still_valid(schema):
    """Backward compat: existing strategy maps without `resolution` still validate."""
    sm = {'approval_mode': 'review', 'slides': [_base_slide()]}
    jsonschema.validate(sm, schema)


def test_render_funnel_rejects_unknown_stage(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{
            **_base_slide(),
            'render_funnel': ['ollama', 'cloud_xtreme'],
        }],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(sm, schema)


# --- brand_fidelity field (issue #61) ---


def test_brand_fidelity_exact_allowed(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'brand_fidelity': 'exact'}],
    }
    jsonschema.validate(sm, schema)


def test_brand_fidelity_approximate_allowed(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'brand_fidelity': 'approximate'}],
    }
    jsonschema.validate(sm, schema)


def test_brand_fidelity_none_allowed(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'brand_fidelity': 'none'}],
    }
    jsonschema.validate(sm, schema)


def test_invalid_brand_fidelity_rejected(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'brand_fidelity': 'maximum'}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(sm, schema)


def test_brand_fidelity_omitted_still_valid(schema):
    """Backward compat: brand_fidelity is optional."""
    sm = {'approval_mode': 'review', 'slides': [_base_slide()]}
    jsonschema.validate(sm, schema)
