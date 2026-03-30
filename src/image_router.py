"""Image routing matrix, fallback chains, and asset classification.

This module contains the pure routing logic for the imagegen-bridge skill.
It maps visual_type + mode + available providers + budget state to a
RoutingDecision that tells the bridge which skill to invoke.

The routing matrix is derived from research/05-multi-model-routing-pipeline.md
Finding 1.1, with fallback chains from Finding 5.2 and budget degradation
from research/13-cost-optimisation-caching.md Section 4.
"""

from collections import namedtuple


RoutingTarget = namedtuple('RoutingTarget', [
    'skill',           # skill name: 'ollama-image', 'cloud-generate-image', etc.
    'provider',        # provider key: 'ollama', 'openai', 'google', 'fal', 'recraft', 'local'
    'model',           # model identifier: 'x/z-image-turbo', 'gpt-image-1.5', etc.
    'cost_per_image',  # estimated USD cost
])

RoutingDecision = namedtuple('RoutingDecision', [
    'slide_number',    # which slide this is for
    'visual_type',     # classified visual type
    'skill',           # chosen skill name
    'provider',        # chosen provider
    'model',           # chosen model
    'cost_per_image',  # estimated cost
    'is_fallback',     # whether this was a fallback choice
])

UpgradeDecision = namedtuple('UpgradeDecision', [
    'slide_number',
    'image_id',
    'action',           # 'upgrade' or 'keep'
    'reason',
    'draft_prompt',     # carried from draft manifest (None if absent)
    'target_provider',  # provider for upgrade (None if keep)
    'target_model',     # model for upgrade (None if keep)
    'target_size',      # size string e.g. '1536x1024' (None if keep)
    'estimated_cost_usd',
])


# --- Routing Matrix ---
# Maps (visual_type, mode) -> list of RoutingTargets in priority order.
# The first target whose provider is available is selected.

ROUTING_MATRIX = {
    ('hero_image', 'draft'): [
        RoutingTarget('ollama-image', 'ollama', 'x/z-image-turbo', 0.00),
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
        RoutingTarget('cloud-generate-image', 'openai', 'gpt-image-1.5-low', 0.009),
    ],
    ('hero_image', 'production'): [
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
        RoutingTarget('cloud-generate-image', 'openai', 'gpt-image-1.5-med', 0.034),
        RoutingTarget('cloud-generate-image', 'google', 'imagen-4-standard', 0.04),
        RoutingTarget('ollama-image', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('icon_set', 'draft'): [
        RoutingTarget('cloud-generate-icon', 'recraft', 'recraft-v4-svg', 0.08),
        RoutingTarget('cloud-generate-icon', 'fal', 'recraft-v4', 0.08),
    ],
    ('icon_set', 'production'): [
        RoutingTarget('cloud-generate-icon', 'recraft', 'recraft-v4-svg', 0.08),
        RoutingTarget('cloud-generate-icon', 'fal', 'recraft-v4', 0.08),
    ],
    ('pattern_background', 'draft'): [
        RoutingTarget('ollama-pattern', 'ollama', 'x/z-image-turbo', 0.00),
        RoutingTarget('cloud-generate-image', 'google', 'imagen-4-fast', 0.02),
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
    ],
    ('pattern_background', 'production'): [
        RoutingTarget('cloud-generate-image', 'google', 'imagen-4-fast', 0.02),
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
        RoutingTarget('ollama-pattern', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('diagram', 'draft'): [
        RoutingTarget('ollama-diagram', 'ollama', 'x/flux2-klein', 0.00),
    ],
    ('diagram', 'production'): [
        RoutingTarget('ollama-diagram', 'ollama', 'x/flux2-klein', 0.00),
    ],
    ('chart', 'draft'): [
        RoutingTarget('render_chart', 'local', 'matplotlib', 0.00),
    ],
    ('chart', 'production'): [
        RoutingTarget('render_chart', 'local', 'matplotlib', 0.00),
    ],
    ('none', 'draft'): [],
    ('none', 'production'): [],
}

# Budget-degraded routing overrides
BUDGET_DEGRADED_MATRIX = {
    ('hero_image', 'allow_with_caps'): [
        RoutingTarget('cloud-generate-image', 'google', 'imagen-4-fast', 0.02),
        RoutingTarget('cloud-generate-image', 'fal', 'flux-2-pro', 0.03),
        RoutingTarget('ollama-image', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('hero_image', 'degrade'): [
        RoutingTarget('ollama-image', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('icon_set', 'allow_with_caps'): [
        RoutingTarget('cloud-generate-icon', 'recraft', 'recraft-v4-svg', 0.08),
    ],
    ('icon_set', 'degrade'): [],  # No local alternative for SVG icons
    ('pattern_background', 'allow_with_caps'): [
        RoutingTarget('ollama-pattern', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('pattern_background', 'degrade'): [
        RoutingTarget('ollama-pattern', 'ollama', 'x/z-image-turbo', 0.00),
    ],
    ('diagram', 'allow_with_caps'): [
        RoutingTarget('ollama-diagram', 'ollama', 'x/flux2-klein', 0.00),
    ],
    ('diagram', 'degrade'): [
        RoutingTarget('ollama-diagram', 'ollama', 'x/flux2-klein', 0.00),
    ],
}

# Slide type to visual type inference (when visual_type is missing)
SLIDE_TYPE_TO_VISUAL_TYPE = {
    'title': 'hero_image',
    'section_divider': 'pattern_background',
    'content': 'none',
    'two_column': 'none',
    'image_feature': 'hero_image',
    'data_chart': 'chart',
    'stat_callout': 'pattern_background',
    'quote': 'pattern_background',
    'icon_grid': 'icon_set',
    'diagram': 'diagram',
    'closing': 'none',
    'blank_visual': 'hero_image',
}

VALID_VISUAL_TYPES = {'hero_image', 'icon_set', 'pattern_background', 'diagram', 'chart', 'none'}

# Models/tools that already produce high-quality output
_PRODUCTION_QUALITY_SOURCES = {'svg-convert', 'matplotlib', 'render_chart'}

# Visual types that benefit from cloud upgrade
_UPGRADEABLE_VISUAL_TYPES = {'hero_image', 'pattern_background', 'icon_set'}


def classify_visual_type(slide):
    """Classify a slide's visual type from its visual_type field or slide_type.

    Args:
        slide: dict with at least 'slide_type' and optionally 'visual_type'.

    Returns:
        One of: 'hero_image', 'icon_set', 'pattern_background', 'diagram', 'chart', 'none'.
    """
    visual_type = slide.get('visual_type')
    if visual_type and visual_type in VALID_VISUAL_TYPES:
        return visual_type
    slide_type = slide.get('slide_type', 'content')
    return SLIDE_TYPE_TO_VISUAL_TYPE.get(slide_type, 'none')


def _is_provider_available(provider, available_providers):
    """Check if a provider is available."""
    if provider == 'local':
        return True
    provider_info = available_providers.get(provider, {})
    if isinstance(provider_info, dict):
        return provider_info.get('available', False)
    return False


def route_slide(slide, mode, available_providers, budget_state):
    """Route a single slide to the appropriate generation skill.

    Args:
        slide: dict from SlideOutline with at least slide_number, visual_type.
        mode: 'draft' or 'production'.
        available_providers: dict from provider_discovery.
        budget_state: one of 'allow', 'allow_with_caps', 'degrade', 'typography_only'.

    Returns:
        RoutingDecision namedtuple.
    """
    slide_number = slide.get('slide_number', 0)
    visual_type = classify_visual_type(slide)

    if visual_type == 'none':
        return RoutingDecision(
            slide_number=slide_number,
            visual_type='none',
            skill='skip',
            provider='none',
            model='none',
            cost_per_image=0.0,
            is_fallback=False,
        )

    # Charts always route to render_chart regardless of budget
    if visual_type == 'chart':
        return RoutingDecision(
            slide_number=slide_number,
            visual_type='chart',
            skill='render_chart',
            provider='local',
            model='matplotlib',
            cost_per_image=0.0,
            is_fallback=False,
        )

    # Typography-only: placeholder for everything except charts
    if budget_state == 'typography_only':
        return RoutingDecision(
            slide_number=slide_number,
            visual_type=visual_type,
            skill='placeholder',
            provider='none',
            model='none',
            cost_per_image=0.0,
            is_fallback=True,
        )

    # Select routing targets based on budget state
    if budget_state in ('allow_with_caps', 'degrade'):
        targets = BUDGET_DEGRADED_MATRIX.get(
            (visual_type, budget_state),
            ROUTING_MATRIX.get((visual_type, mode), [])
        )
    else:
        targets = ROUTING_MATRIX.get((visual_type, mode), [])

    # Find first available target
    is_fallback = False
    for target in targets:
        if _is_provider_available(target.provider, available_providers):
            return RoutingDecision(
                slide_number=slide_number,
                visual_type=visual_type,
                skill=target.skill,
                provider=target.provider,
                model=target.model,
                cost_per_image=target.cost_per_image,
                is_fallback=is_fallback,
            )
        is_fallback = True

    # No targets available: try the full fallback chain from normal routing
    if budget_state in ('allow_with_caps', 'degrade'):
        normal_targets = ROUTING_MATRIX.get((visual_type, mode), [])
        for target in normal_targets:
            # In degrade mode, only fall back to free (local/ollama) providers
            if budget_state == 'degrade' and target.cost_per_image > 0:
                continue
            if _is_provider_available(target.provider, available_providers):
                return RoutingDecision(
                    slide_number=slide_number,
                    visual_type=visual_type,
                    skill=target.skill,
                    provider=target.provider,
                    model=target.model,
                    cost_per_image=target.cost_per_image,
                    is_fallback=True,
                )

    # All fallbacks exhausted: placeholder
    return RoutingDecision(
        slide_number=slide_number,
        visual_type=visual_type,
        skill='placeholder',
        provider='none',
        model='none',
        cost_per_image=0.0,
        is_fallback=True,
    )


def route_all_slides(outline, mode, available_providers, budget_state):
    """Route all slides in an outline to generation skills.

    Excludes chart slides (handled separately by get_chart_slides).

    Args:
        outline: dict with 'slides' array from SlideOutline.
        mode: 'draft' or 'production'.
        available_providers: dict from provider_discovery.
        budget_state: one of 'allow', 'allow_with_caps', 'degrade', 'typography_only'.

    Returns:
        List of RoutingDecision namedtuples.
    """
    decisions = []
    for slide in outline.get('slides', []):
        visual_type = classify_visual_type(slide)
        if visual_type == 'chart':
            continue
        decision = route_slide(slide, mode, available_providers, budget_state)
        decisions.append(decision)
    return decisions


def get_chart_slides(outline):
    """Extract slides that need chart rendering.

    Args:
        outline: dict with 'slides' array from SlideOutline.

    Returns:
        List of slide dicts where visual_type is 'chart'.
    """
    charts = []
    for slide in outline.get('slides', []):
        visual_type = classify_visual_type(slide)
        if visual_type == 'chart':
            charts.append(slide)
    return charts


def generate_placeholder_color(palette, visual_type):
    """Pick an appropriate placeholder colour from the StyleGuide palette.

    Args:
        palette: dict with palette colours (6-char hex without #).
        visual_type: the visual type that failed generation.

    Returns:
        6-char hex colour string.
    """
    colour_map = {
        'hero_image': 'background_alt',
        'pattern_background': 'primary',
        'diagram': 'background_alt',
        'icon_set': 'secondary',
    }
    key = colour_map.get(visual_type, 'primary')
    return palette.get(key, palette.get('primary', '333333'))


def plan_production_upgrade(draft_manifest, outline, available_providers, budget_state):
    """Plan which images to upgrade from draft to production quality.

    Args:
        draft_manifest: dict from image-manifest.json.
        outline: dict from outline.json with 'slides' array.
        available_providers: dict from provider_discovery.
        budget_state: dict with 'budget_state' and 'remaining_usd'.

    Returns:
        list[UpgradeDecision]: One decision per manifest entry.
    """
    remaining = budget_state.get('remaining_usd', 0.0)
    slide_types = {
        s['slide_number']: classify_visual_type(s)
        for s in outline.get('slides', [])
    }

    decisions = []
    for entry in draft_manifest.get('images', []):
        slide_num = entry.get('slide_number', 0)
        image_id = entry.get('image_id', '')
        model_used = entry.get('model_used', '')
        visual_type = slide_types.get(slide_num, 'none')
        draft_prompt = entry.get('source_prompt')

        # Already production quality?
        if model_used in _PRODUCTION_QUALITY_SOURCES:
            decisions.append(UpgradeDecision(
                slide_number=slide_num,
                image_id=image_id,
                action='keep',
                reason=f'Already production quality ({model_used})',
                draft_prompt=draft_prompt,
                target_provider=None,
                target_model=None,
                target_size=None,
                estimated_cost_usd=0.0,
            ))
            continue

        # Not a type that benefits from upgrade?
        if visual_type not in _UPGRADEABLE_VISUAL_TYPES:
            decisions.append(UpgradeDecision(
                slide_number=slide_num,
                image_id=image_id,
                action='keep',
                reason=f'Visual type {visual_type} does not benefit from cloud upgrade',
                draft_prompt=draft_prompt,
                target_provider=None,
                target_model=None,
                target_size=None,
                estimated_cost_usd=0.0,
            ))
            continue

        # Find the best production route
        route = route_slide(
            {'slide_number': slide_num, 'visual_type': visual_type},
            'production',
            available_providers,
            budget_state.get('budget_state', 'allow'),
        )

        # Budget check
        if route.cost_per_image > remaining:
            decisions.append(UpgradeDecision(
                slide_number=slide_num,
                image_id=image_id,
                action='keep',
                reason=f'Upgrade cost ${route.cost_per_image:.3f} exceeds remaining ${remaining:.2f}',
                draft_prompt=draft_prompt,
                target_provider=None,
                target_model=None,
                target_size=None,
                estimated_cost_usd=0.0,
            ))
            continue

        remaining -= route.cost_per_image
        decisions.append(UpgradeDecision(
            slide_number=slide_num,
            image_id=image_id,
            action='upgrade',
            reason=f'{visual_type} benefits from cloud quality',
            draft_prompt=draft_prompt,
            target_provider=route.provider,
            target_model=route.model,
            target_size='1536x1024',
            estimated_cost_usd=route.cost_per_image,
        ))

    return decisions
