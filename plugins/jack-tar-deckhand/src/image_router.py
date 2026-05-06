"""Image routing matrix, fallback chains, and asset classification.

This module contains the pure routing logic for the imagegen-bridge skill.
It maps visual_type + mode + available providers + budget state to a
RoutingDecision that tells the bridge which skill to invoke.

The routing matrix is derived from research/05-multi-model-routing-pipeline.md
Finding 1.1, with fallback chains from Finding 5.2 and budget degradation
from research/13-cost-optimisation-caching.md Section 4.
"""

import json
import os
from collections import namedtuple


RoutingTarget = namedtuple(
    'RoutingTarget',
    [
        'skill',           # skill name: 'ollama-image', 'cloud-generate-image', etc.
        'provider',        # provider key: 'ollama', 'openai', 'google', 'fal', 'recraft', 'local'
        'model',           # model identifier: 'x/z-image-turbo', 'gpt-image-1.5', etc.
        'cost_per_image',  # estimated USD cost
        'resolution',      # '1K'/'2K'/'4K' tier (defaults to '1K' for back-compat)
    ],
    defaults=['1K'],
)

RoutingDecision = namedtuple(
    'RoutingDecision',
    [
        'slide_number',    # which slide this is for
        'visual_type',     # classified visual type
        'skill',           # chosen skill name
        'provider',        # chosen provider
        'model',           # chosen model
        'cost_per_image',  # estimated cost
        'is_fallback',     # whether this was a fallback choice
        'resolution',      # '1K'/'2K'/'4K' tier (defaults to '1K')
    ],
    defaults=['1K'],
)

UpgradeDecision = namedtuple(
    'UpgradeDecision',
    [
        'slide_number',
        'image_id',
        'action',           # 'upgrade' or 'keep'
        'reason',
        'draft_prompt',     # carried from draft manifest (None if absent)
        'target_provider',  # provider for upgrade (None if keep)
        'target_model',     # model for upgrade (None if keep)
        'target_size',      # size string e.g. '1536x1024' (None if keep)
        'target_resolution',  # '1K'/'2K'/'4K' tier (defaults to '1K')
        'estimated_cost_usd',
        'warnings',         # list of warning strings (empty list if none)
    ],
    defaults=['1K', 0.0, []],
)


# --- Routing Matrix ---
# Maps (visual_type, mode) -> list of RoutingTargets in priority order.
# The first target whose provider is available is selected.

# ROUTING_MATRIX keys: (visual_type, mode). Within each row, RoutingTargets
# are listed in priority order — the first available provider wins. Ordering
# is quality-first, then cost-ascending where quality is comparable. For
# example, the 2K hero row leads with Nano Banana Flash (best text rendering
# in the tier despite higher cost), then FAL FLUX 2 Pro (photo workhorse),
# then Imagen Standard (budget fallback).
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
    ('hero_image', 'production_2k'): [
        RoutingTarget('cloud-generate-image', 'google', 'gemini-3.1-flash-image-preview', 0.101, '2K'),
        RoutingTarget('cloud-generate-image', 'fal', 'fal-ai/flux-2-pro', 0.075, '2K'),
        RoutingTarget('cloud-generate-image', 'google', 'imagen-4.0-generate-001', 0.04, '2K'),
    ],
    ('hero_image', 'production_4k'): [
        RoutingTarget('cloud-generate-image', 'google', 'gemini-3-pro-image-preview', 0.24, '4K'),
        RoutingTarget('cloud-generate-image', 'google', 'gemini-3.1-flash-image-preview', 0.151, '4K'),
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
        RoutingTarget('cloud-generate-icon', 'recraft', 'recraft-v4-svg', 0.08),
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
_UPGRADEABLE_VISUAL_TYPES = {'hero_image', 'pattern_background', 'icon_set', 'diagram'}

# OpenAI GPT Image only supports these fixed sizes
OPENAI_SUPPORTED_SIZES = {'1024x1024', '1536x1024', '1024x1536'}

# Per-provider/model resolution capability for in-process pre-validation.
#
# Two kinds of entries:
#   1. Canonical model IDs — must stay byte-identical to the cloud plugin's
#      authoritative source. Cross-plugin drift detection in
#      plugins/integration_tests/test_router_capability_drift.py asserts
#      these match plugins/jack-tar-cloud/src/provider_discovery.py's
#      _PROVIDER_MODEL_RESOLUTIONS for every model that appears in both.
#   2. Router-internal aliases (gpt-image-1.5-low, imagen-4-fast,
#      imagen-4-standard, flux-2-pro) used in ROUTING_MATRIX rows for
#      readability. These translate to canonical IDs at dispatch time
#      (see imagegen-bridge SKILL.md). Aliases have no cloud-plugin
#      counterpart and are not subject to drift checking.
#
# Single source of truth at runtime is provider_discovery.discover_providers(),
# which exposes the canonical capability via available_providers[provider]
# ['models'][model]['supported_resolutions']. This static table is for
# router-time decisions where reaching across plugin boundaries would
# require a live cloud-plugin import.
_PROVIDER_MODEL_RESOLUTIONS = {
    ('openai', 'gpt-image-1.5'): ['1K'],
    ('openai', 'gpt-image-1.5-low'): ['1K'],
    ('openai', 'gpt-image-1.5-med'): ['1K'],
    ('google', 'imagen-4-fast'): ['1K'],
    ('google', 'imagen-4.0-fast-generate-001'): ['1K'],
    ('google', 'imagen-4-standard'): ['1K', '2K'],
    ('google', 'imagen-4.0-generate-001'): ['1K', '2K'],
    ('google', 'imagen-4.0-ultra-generate-001'): ['1K', '2K'],
    ('google', 'gemini-3.1-flash-image-preview'): ['512', '1K', '2K', '4K'],
    ('google', 'gemini-3-pro-image-preview'): ['1K', '2K', '4K'],
    ('fal', 'fal-ai/flux-2-pro'): ['1K', '2K'],
    ('fal', 'flux-2-pro'): ['1K', '2K'],
    ('fal', 'fal-ai/flux-2-klein'): ['1K'],
    ('fal', 'fal-ai/ideogram/v3'): ['1K'],
}


def _check_resolution_compatibility(provider, model, resolution):
    """Return a warning string if provider/model doesn't support the tier.

    Returns None if the tier is supported or the provider/model is unknown
    (unknown is not an error — the underlying call will surface the failure).
    """
    if not resolution:
        return None
    supported = _PROVIDER_MODEL_RESOLUTIONS.get((provider, model))
    if supported is None:
        return None  # unknown — let the cloud plugin surface the error
    if resolution in supported:
        return None
    return (
        f"{provider}/{model} does not support resolution={resolution!r}. "
        f"Supported tiers: {supported}. "
        f"Pick a different model or downgrade the slide's resolution request."
    )


def _check_openai_dimension_warning(provider, target_dims):
    """Return a warning string if OpenAI is the provider and dims are non-standard.

    Args:
        provider: provider key string (e.g. 'openai').
        target_dims: target dimensions string (e.g. '1920x1080') or None.

    Returns:
        Warning string if applicable, otherwise None.
    """
    if provider != 'openai':
        return None
    if target_dims is None:
        return None
    if target_dims in OPENAI_SUPPORTED_SIZES:
        return None
    return (
        f'OpenAI supports only 1024x1024, 1536x1024, 1024x1536. '
        f'Target {target_dims} requires cropping or a different provider '
        f'(FLUX Pro supports arbitrary dimensions).'
    )


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
            resolution='1K',
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
            resolution='1K',
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
            resolution='1K',
        )

    # Resolution-aware mode upgrade: a slide-level resolution hint upgrades
    # the mode key so we hit the high-res routing rows in ROUTING_MATRIX.
    requested_resolution = slide.get('resolution', '1K')
    effective_mode = mode
    if mode == 'production' and requested_resolution in ('2K', '4K'):
        effective_mode = f'production_{requested_resolution.lower()}'

    # Select routing targets based on budget state
    if budget_state in ('allow_with_caps', 'degrade'):
        targets = BUDGET_DEGRADED_MATRIX.get(
            (visual_type, budget_state),
            ROUTING_MATRIX.get((visual_type, effective_mode), [])
        )
    else:
        targets = ROUTING_MATRIX.get((visual_type, effective_mode), [])

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
                resolution=getattr(target, 'resolution', '1K'),
            )
        is_fallback = True

    # No targets available: try the full fallback chain from normal routing
    if budget_state in ('allow_with_caps', 'degrade'):
        normal_targets = ROUTING_MATRIX.get((visual_type, effective_mode), [])
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
                    resolution=getattr(target, 'resolution', '1K'),
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
        resolution='1K',
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
                target_resolution='1K',
                estimated_cost_usd=0.0,
                warnings=[],
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
                target_resolution='1K',
                estimated_cost_usd=0.0,
                warnings=[],
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
                target_resolution='1K',
                estimated_cost_usd=0.0,
                warnings=[],
            ))
            continue

        remaining -= route.cost_per_image
        target_size = '1536x1024'
        warnings = []
        dim_warning = _check_openai_dimension_warning(route.provider, target_size)
        if dim_warning:
            warnings.append(dim_warning)
        res_warning = _check_resolution_compatibility(
            route.provider, route.model, getattr(route, 'resolution', '1K'),
        )
        if res_warning:
            warnings.append(res_warning)
        decisions.append(UpgradeDecision(
            slide_number=slide_num,
            image_id=image_id,
            action='upgrade',
            reason=f'{visual_type} benefits from cloud quality',
            draft_prompt=draft_prompt,
            target_provider=route.provider,
            target_model=route.model,
            target_size=target_size,
            target_resolution=getattr(route, 'resolution', '1K'),
            estimated_cost_usd=route.cost_per_image,
            warnings=warnings,
        ))

    return decisions


def load_upgrade_plan(deck_dir):
    """Load the expert-approved production-upgrade-plan.json.

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        dict: The parsed production upgrade plan.

    Raises:
        FileNotFoundError: If production-upgrade-plan.json does not exist.
    """
    path = os.path.join(deck_dir, 'production-upgrade-plan.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'No production-upgrade-plan.json in {deck_dir}')
    with open(path) as f:
        return json.load(f)


def execute_upgrade_plan_entry(entry):
    """Map a single upgrade plan entry to execution parameters.

    Args:
        entry: dict from the production upgrade plan entries array.

    Returns:
        dict: {skill, provider, model, width, height} for the imagegen-bridge
              to execute. width/height are None for vector_conversion and no_upgrade.
    """
    track = entry['upgrade_track']

    if track == 'no_upgrade':
        return {
            'skill': 'skip',
            'provider': entry.get('recommended_provider', 'none'),
            'model': entry.get('recommended_model', 'none'),
            'width': None,
            'height': None,
        }

    if track == 'vector_conversion':
        return {
            'skill': 'cloud-generate-icon',
            'provider': entry['recommended_provider'],
            'model': entry['recommended_model'],
            'width': None,
            'height': None,
        }

    # raster_upscale
    dims = entry.get('target_dimensions')
    width, height = None, None
    if dims and 'x' in dims:
        parts = dims.split('x')
        width, height = int(parts[0]), int(parts[1])

    return {
        'skill': 'cloud-generate-image',
        'provider': entry['recommended_provider'],
        'model': entry['recommended_model'],
        'width': width,
        'height': height,
    }


def validate_plan_entry_dimensions(entry):
    """Check a production upgrade plan entry for provider dimension mismatches.

    Mutates the entry's 'warnings' list in place if a mismatch is found.

    Args:
        entry: dict from the production upgrade plan entries array,
               must have 'recommended_provider', 'target_dimensions', 'warnings'.

    Returns:
        The entry (for chaining convenience).
    """
    provider = entry.get('recommended_provider')
    dims = entry.get('target_dimensions')
    warning = _check_openai_dimension_warning(provider, dims)
    if warning:
        entry.setdefault('warnings', []).append(warning)
    return entry
