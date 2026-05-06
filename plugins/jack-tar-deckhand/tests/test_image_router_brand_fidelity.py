"""Brand-fidelity routing: slide.brand_fidelity == 'exact' prefers Recraft."""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src import image_router  # noqa: E402


def test_exact_brand_fidelity_routes_to_recraft():
    slide = {
        'slide_number': 1,
        'visual_type': 'hero_image',
        'brand_fidelity': 'exact',
    }
    available = {
        'google': {'available': True},
        'fal': {'available': True},
        'openai': {'available': True},
        'recraft': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider == 'recraft'


def test_exact_brand_fidelity_4k_routes_to_recraft_pro():
    """A 4K hero with brand_fidelity='exact' must route to Recraft Pro 4K
    even though Nano Banana Pro 4K is cheaper."""
    slide = {
        'slide_number': 1,
        'visual_type': 'hero_image',
        'resolution': '4K',
        'brand_fidelity': 'exact',
    }
    available = {
        'google': {'available': True},
        'recraft': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider == 'recraft'
    assert decision.resolution == '4K'


def test_no_brand_fidelity_keeps_existing_routing():
    """Without brand_fidelity flag, routing is unchanged from #60 behaviour."""
    slide = {
        'slide_number': 1,
        'visual_type': 'hero_image',
        'resolution': '4K',
    }
    available = {
        'google': {'available': True},
        'recraft': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    # 4K Pro = Nano Banana Pro by default (issue #60)
    assert decision.provider == 'google'


def test_approximate_brand_fidelity_keeps_default_routing():
    """'approximate' is documentary; doesn't change routing from default."""
    slide = {
        'slide_number': 1,
        'visual_type': 'hero_image',
        'brand_fidelity': 'approximate',
    }
    available = {
        'fal': {'available': True},
        'recraft': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider == 'fal'  # existing first target for hero production


def test_recraft_unavailable_falls_back_when_brand_fidelity_exact():
    """If brand_fidelity='exact' but recraft is not available, fall through
    to the next-best provider with a warning."""
    slide = {
        'slide_number': 1,
        'visual_type': 'hero_image',
        'brand_fidelity': 'exact',
    }
    available = {
        'google': {'available': True},
        'fal': {'available': True},
        'recraft': {'available': False},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider != 'recraft'
    assert decision.is_fallback is True
