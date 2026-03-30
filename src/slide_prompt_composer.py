"""Slide prompt composer — strategy classification and structured brief assembly.

Analyses each slide in a SlideOutline and:
1. Classifies its rendering strategy (full_render, backdrop_render, composed)
2. Assembles structured briefs for the Prompt Engineer agent
3. Validates output prompts contain required brand elements

Strategy classification is deterministic Python logic. Prompt generation
is delegated to the Prompt Engineer agent (LLM reasoning).
"""

import json
import os

import jsonschema

from src.image_router import classify_visual_type

_SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'schemas')


# Slide types that work well as full AI-rendered images (short text, visual impact)
_FULL_RENDER_TYPES = {'title', 'section_divider', 'closing', 'blank_visual', 'quote'}

# Slide types that must stay programmatic (precise text, data, labels)
_COMPOSED_TYPES = {'data_chart', 'diagram', 'code'}

# Maximum body points before a content slide should use backdrop instead of full render
_BACKDROP_BULLET_THRESHOLD = 2


def classify_slide_strategy(slide):
    """Classify a slide's recommended rendering strategy.

    Args:
        slide: dict from SlideOutline slides array.

    Returns:
        dict with keys: slide_number, strategy, rationale, render_funnel, speaker_override
    """
    slide_number = slide.get('slide_number', 0)
    slide_type = slide.get('slide_type', 'content')
    body_points = slide.get('body_points', [])
    visual_type = classify_visual_type(slide)

    # Charts and diagrams must stay composed (precise text/labels)
    if slide_type in _COMPOSED_TYPES or visual_type == 'chart':
        return {
            'slide_number': slide_number,
            'strategy': 'composed',
            'rationale': f'{slide_type} slide requires precise text/label rendering — programmatic assembly',
            'render_funnel': ['ollama'],
            'speaker_override': None,
        }

    # Short-text slide types are ideal for full render
    if slide_type in _FULL_RENDER_TYPES:
        return {
            'slide_number': slide_number,
            'strategy': 'full_render',
            'rationale': f'{slide_type} slide with short text — ideal for full AI generation',
            'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
            'speaker_override': None,
        }

    # Content slides: backdrop if dense text, full render if sparse
    if len(body_points) > _BACKDROP_BULLET_THRESHOLD:
        return {
            'slide_number': slide_number,
            'strategy': 'backdrop_render',
            'rationale': f'Content slide with {len(body_points)} bullet points — AI background with programmatic text overlay',
            'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
            'speaker_override': None,
        }

    return {
        'slide_number': slide_number,
        'strategy': 'full_render',
        'rationale': f'Content slide with {len(body_points)} bullet points — sparse enough for full AI generation',
        'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
        'speaker_override': None,
    }


from datetime import datetime, timezone


def build_strategy_map(outline, approval_mode='review', overrides=None):
    """Build a complete StrategyMap from a SlideOutline.

    Args:
        outline: dict from SlideOutline (must have 'slides' array).
        approval_mode: 'review' (default) or 'one_shot'.
        overrides: Optional dict of {slide_number: strategy} Speaker overrides.

    Returns:
        dict conforming to StrategyMap schema.
    """
    overrides = overrides or {}
    slides = []

    for slide in outline.get('slides', []):
        entry = classify_slide_strategy(slide)
        slide_num = entry['slide_number']

        if slide_num in overrides:
            entry['speaker_override'] = overrides[slide_num]
            # Override also sets the render funnel for the new strategy
            if overrides[slide_num] in ('full_render', 'backdrop_render'):
                entry['render_funnel'] = ['ollama', 'cloud_low', 'cloud_full']
            else:
                entry['render_funnel'] = ['ollama']

        slides.append(entry)

    return {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'approval_mode': approval_mode,
        'slides': slides,
    }


# Resolution targets per funnel stage
_RESOLUTIONS = {
    'ollama': '1024x576',
    'cloud_low': '1280x720',
    'cloud_full': '1920x1080',
}


def assemble_brief(slide, strategy, style_guide, brand_profile, funnel_stage):
    """Assemble a structured brief for the Prompt Engineer agent.

    Args:
        slide: dict from SlideOutline slides array.
        strategy: 'full_render' or 'backdrop_render'.
        style_guide: dict from StyleGuide contract.
        brand_profile: dict from BrandProfile contract (or None).
        funnel_stage: 'ollama', 'cloud_low', or 'cloud_full'.

    Returns:
        dict: Structured brief with all context the Prompt Engineer needs.
    """
    palette = style_guide.get('palette', {})
    palette_hex = [v for v in palette.values() if isinstance(v, str) and len(v) == 6]

    brand_constraints = {
        'palette_hex': palette_hex,
        'approved_styles': [],
        'prohibited_styles': [],
    }
    if brand_profile:
        brand_constraints['approved_styles'] = brand_profile.get('approved_image_styles', [])
        brand_constraints['prohibited_styles'] = brand_profile.get('prohibited_image_styles', [])

    style_tokens = style_guide.get('image_style_tokens', {})

    brief = {
        'slide_number': slide.get('slide_number', 0),
        'strategy': strategy,
        'headline': slide.get('headline', ''),
        'body_points': slide.get('body_points', []),
        'visual_direction': slide.get('visual_direction', ''),
        'slide_type': slide.get('slide_type', 'content'),
        'brand_constraints': brand_constraints,
        'style_tokens': style_tokens,
        'funnel_stage': funnel_stage,
        'target_resolution': _RESOLUTIONS.get(funnel_stage, '1920x1080'),
    }

    if strategy == 'backdrop_render':
        brief['text_instruction'] = 'NO TEXT in the image \u2014 leave clean space for text overlay'
    elif strategy == 'full_render':
        brief['text_instruction'] = f'Include headline text: "{slide.get("headline", "")}"'

    return brief


def _validate_strategy_map(strategy_map):
    """Validate a strategy map against the JSON schema.

    Args:
        strategy_map: dict to validate.

    Raises:
        jsonschema.ValidationError: If the strategy map does not conform to the schema.
    """
    schema_path = os.path.join(_SCHEMA_DIR, 'strategy_map.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(strategy_map)


def save_strategy_map(deck_dir, strategy_map):
    """Save a strategy map to the DeckContext directory.

    Validates against the StrategyMap schema before writing.
    Uses an atomic write (write to .tmp then os.replace) to avoid
    partial writes.

    Args:
        deck_dir: Path to the deck working directory.
        strategy_map: dict conforming to StrategyMap schema.

    Raises:
        jsonschema.ValidationError: If strategy_map is invalid.
    """
    _validate_strategy_map(strategy_map)
    path = os.path.join(deck_dir, 'strategy-map.json')
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(strategy_map, f, indent=2)
        f.write('\n')
    os.replace(tmp_path, path)


def load_strategy_map(deck_dir):
    """Load a strategy map from the DeckContext directory.

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        dict: The parsed strategy map.

    Raises:
        FileNotFoundError: If strategy-map.json does not exist in deck_dir.
    """
    path = os.path.join(deck_dir, 'strategy-map.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'No strategy-map.json in {deck_dir}')
    with open(path) as f:
        return json.load(f)
