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
_COMPOSED_TYPES = {'data_chart', 'code'}

# Maximum body points before a content slide should use backdrop instead of full render
_BACKDROP_BULLET_THRESHOLD = 2


def classify_slide_strategy(slide, template_mode=False, template_layout=None):
    """Classify a slide's recommended rendering strategy.

    Args:
        slide: dict from SlideOutline slides array.
        template_mode: If True, constrain strategy to composed unless a full-bleed
            picture placeholder is detected in template_layout.
        template_layout: Optional dict with 'placeholders' list describing the
            template's placeholder regions (requires 'type', 'w', 'h' per entry).

    Returns:
        dict with keys: slide_number, strategy, rationale, render_funnel, speaker_override
    """
    slide_number = slide.get('slide_number', 0)
    slide_type = slide.get('slide_type', 'content')
    body_points = slide.get('body_points', [])
    visual_type = classify_visual_type(slide)

    # Template mode: constrain to composed, except full-bleed picture layouts
    if template_mode:
        if template_layout:
            slide_area = 13.333 * 7.5  # standard 16:9
            for ph in template_layout.get('placeholders', []):
                if ph['type'] == 'picture':
                    ph_area = ph['w'] * ph['h']
                    if ph_area / slide_area > 0.9:
                        return {
                            'slide_number': slide_number,
                            'strategy': 'full_render',
                            'rationale': 'Template layout has full-bleed picture placeholder',
                            'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
                            'speaker_override': None,
                        }
        return {
            'slide_number': slide_number,
            'strategy': 'composed',
            'rationale': 'Template mode — content placed in template placeholders',
            'render_funnel': ['ollama'],
            'speaker_override': None,
        }

    # Diagram slides route to SmartArt assembly (pptx_native placeholders)
    if slide_type == 'diagram':
        return {
            'slide_number': slide_number,
            'strategy': 'smartart',
            'rationale': 'diagram slide — routed to SmartArt assembly for editable graphics',
            'render_funnel': ['ollama'],
            'speaker_override': None,
        }

    # Charts and code must stay composed (precise text/labels)
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

    # Content slides: background if dense text, full render if sparse
    if len(body_points) > _BACKDROP_BULLET_THRESHOLD:
        return {
            'slide_number': slide_number,
            'strategy': 'background',
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


def build_strategy_map(outline, approval_mode='review', overrides=None, template_mode=False):
    """Build a complete StrategyMap from a SlideOutline.

    Args:
        outline: dict from SlideOutline (must have 'slides' array).
        approval_mode: 'review' (default) or 'one_shot'.
        overrides: Optional dict of {slide_number: strategy} Speaker overrides.
        template_mode: If True, pass template_mode=True to classify_slide_strategy
            for every slide, constraining strategies to composed.

    Returns:
        dict conforming to StrategyMap schema.
    """
    overrides = overrides or {}
    slides = []

    for slide in outline.get('slides', []):
        entry = classify_slide_strategy(slide, template_mode=template_mode)
        slide_num = entry['slide_number']

        if slide_num in overrides:
            entry['speaker_override'] = overrides[slide_num]
            # Override also sets the render funnel for the new strategy
            if overrides[slide_num] in ('full_render', 'backdrop_render', 'background', 'backdrop'):
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


def assemble_brief(slide, strategy, style_guide, brand_profile, funnel_stage,
                   backdrop_variant=None, element_layout=None):
    """Assemble a structured brief for the Prompt Engineer agent.

    Args:
        slide: dict from SlideOutline slides array.
        strategy: Strategy string (full_render, background, backdrop, pragmatic_composition, composed).
        style_guide: dict from StyleGuide contract.
        brand_profile: dict from BrandProfile contract (or None).
        funnel_stage: 'ollama', 'cloud_low', or 'cloud_full'.
        backdrop_variant: Template zone name for background strategy (optional).
        element_layout: Element layout dict for backdrop/pragmatic strategies (optional).

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

    if strategy in ('backdrop_render', 'background', 'backdrop', 'pragmatic_composition'):
        brief['text_instruction'] = 'NO TEXT in the image \u2014 leave clean space for text overlay'
    elif strategy == 'full_render':
        brief['text_instruction'] = f'Include headline text: "{slide.get("headline", "")}"'

    if backdrop_variant:
        brief['backdrop_variant'] = backdrop_variant

    if element_layout:
        brief['element_layout'] = element_layout

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


_ELEMENT_LAYOUTS = {
    'three_across': {
        'regions': lambda n: [
            {'x': 0.05 + i * 0.32, 'y': 0.22, 'w': 0.27, 'h': 0.50}
            for i in range(n)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.12},
    },
    'two_column': {
        'regions': lambda n: [
            {'x': 0.05 + i * 0.50, 'y': 0.22, 'w': 0.42, 'h': 0.55}
            for i in range(n)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.12},
    },
    'grid_2x2': {
        'regions': lambda n: [
            {'x': 0.05 + (i % 2) * 0.50, 'y': 0.18 + (i // 2) * 0.40, 'w': 0.42, 'h': 0.35}
            for i in range(n)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.10},
    },
    'process_flow': {
        'regions': lambda n: [
            {'x': 0.03 + i * (0.94 / n), 'y': 0.25, 'w': 0.94 / n - 0.03, 'h': 0.45}
            for i in range(n)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.12},
    },
    'hub_and_spoke': {
        'regions': lambda n: [
            {'x': 0.37, 'y': 0.28, 'w': 0.26, 'h': 0.40},  # centre hub
        ] + [
            {'x': [0.05, 0.70, 0.05, 0.70][i], 'y': [0.15, 0.15, 0.55, 0.55][i], 'w': 0.22, 'h': 0.28}
            for i in range(n - 1)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.10},
    },
}


def get_element_layout(template_name, element_count):
    """Return an element_layout dict for the given template and count.

    Args:
        template_name: One of 'three_across', 'two_column', 'grid_2x2',
                       'process_flow', 'hub_and_spoke'.
        element_count: Number of elements (1-5).

    Returns:
        dict with 'template', 'elements' (array of {id, label_source, x, y, w, h}),
        and 'title_region'.

    Raises:
        ValueError: If element_count > 5 or template_name unknown.
    """
    if element_count > 5:
        raise ValueError(f'Element count {element_count} exceeds maximum of 5')
    if template_name not in _ELEMENT_LAYOUTS:
        raise ValueError(f'Unknown layout template: {template_name}')

    tmpl = _ELEMENT_LAYOUTS[template_name]
    regions = tmpl['regions'](element_count)

    elements = []
    for i, region in enumerate(regions):
        elements.append({
            'id': f'elem_{i + 1}',
            'label_source': f'body_points[{i}]',
            **region,
        })

    return {
        'template': template_name,
        'elements': elements,
        'title_region': tmpl['title_region'],
    }


_BACKDROP_VARIANTS = ['left_panel', 'bottom_bar', 'right_panel', 'top_band', 'center_float']


def select_backdrop_variant(slide_index, total_slides):
    """Select a backdrop variant for visual rhythm.

    Cycles through variants to avoid consecutive duplicates.

    Args:
        slide_index: 0-based index of this slide among background slides.
        total_slides: Total number of slides in the deck (unused, for future weighting).

    Returns:
        str: One of 'left_panel', 'right_panel', 'bottom_bar', 'top_band', 'center_float'.
    """
    return _BACKDROP_VARIANTS[slide_index % len(_BACKDROP_VARIANTS)]


def split_element_briefs(slide, style_guide, brand_profile, element_layout, funnel_stage):
    """Split a slide into 1 background brief + N element briefs for pragmatic composition.

    Args:
        slide: dict from SlideOutline.
        style_guide: StyleGuide dict.
        brand_profile: BrandProfile dict (or None).
        element_layout: Element layout dict with 'elements' array.
        funnel_stage: 'ollama', 'cloud_low', or 'cloud_full'.

    Returns:
        list of brief dicts: [background_brief, elem_1_brief, elem_2_brief, ...]
    """
    palette = style_guide.get('palette', {})
    palette_hex = [v for v in palette.values() if isinstance(v, str) and len(v) == 6]
    style_tokens = style_guide.get('image_style_tokens', {})

    approved = []
    prohibited = []
    if brand_profile:
        approved = brand_profile.get('approved_image_styles', [])
        prohibited = brand_profile.get('prohibited_image_styles', [])

    shared_prefix = (
        f"Brand palette: {', '.join(f'#{h}' for h in palette_hex[:5])}. "
        f"Style: {style_tokens.get('mood', 'professional')}. "
        f"Flat illustration, clean edges, consistent style."
    )

    resolution = _RESOLUTIONS.get(funnel_stage, '1920x1080')

    # Background brief
    bg_brief = {
        'slide_number': slide.get('slide_number', 0),
        'role': 'background',
        'element_id': None,
        'strategy': 'pragmatic_composition',
        'visual_direction': f"Atmospheric textured background. {style_tokens.get('color_direction', '')}. No figurative elements, no objects. Subtle, non-distracting.",
        'text_instruction': 'NO TEXT in the image — pure background texture',
        'brand_constraints': {'palette_hex': palette_hex, 'approved_styles': approved, 'prohibited_styles': prohibited},
        'shared_style_prefix': shared_prefix,
        'funnel_stage': funnel_stage,
        'target_resolution': resolution,
    }

    briefs = [bg_brief]

    # Element briefs
    body_points = slide.get('body_points', [])
    for elem in element_layout.get('elements', []):
        idx_str = elem.get('label_source', 'body_points[0]')
        try:
            idx = int(idx_str.split('[')[1].rstrip(']'))
            label = body_points[idx] if idx < len(body_points) else elem['id']
        except (IndexError, ValueError):
            label = elem['id']

        elem_brief = {
            'slide_number': slide.get('slide_number', 0),
            'role': 'element',
            'element_id': elem['id'],
            'strategy': 'pragmatic_composition',
            'visual_direction': f"Single illustration of: {label}. {slide.get('visual_direction', '')}",
            'text_instruction': 'NO TEXT in the image — the label will be added programmatically',
            'brand_constraints': {'palette_hex': palette_hex, 'approved_styles': approved, 'prohibited_styles': prohibited},
            'shared_style_prefix': shared_prefix,
            'funnel_stage': funnel_stage,
            'target_resolution': resolution,
            'target_dimensions': {
                'w': round(elem['w'] * int(resolution.split('x')[0])),
                'h': round(elem['h'] * int(resolution.split('x')[1])),
            },
        }
        briefs.append(elem_brief)

    return briefs
