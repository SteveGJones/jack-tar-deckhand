"""Slide prompt composer — strategy classification and structured brief assembly.

Analyses each slide in a SlideOutline and:
1. Classifies its rendering strategy (full_render, backdrop_render, composed)
2. Assembles structured briefs for the Prompt Engineer agent
3. Validates output prompts contain required brand elements

Strategy classification is deterministic Python logic. Prompt generation
is delegated to the Prompt Engineer agent (LLM reasoning).
"""

from src.image_router import classify_visual_type


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
