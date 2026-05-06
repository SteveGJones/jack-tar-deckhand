"""End-to-end: a slide with brand_fidelity='exact' routes through deckhand
router to Recraft V4 raster (and the cloud plugin actually has the provider
function wired to dispatch on provider='recraft')."""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent / 'jack-tar-deckhand'


def test_brand_fidelity_exact_routes_to_recraft():
    """A hero slide marked brand_fidelity='exact' must route to Recraft V4 Pro."""
    from src import image_router

    slide = {
        'slide_number': 1,
        'visual_type': 'hero_image',
        'brand_fidelity': 'exact',
    }
    available = {
        'recraft': {'available': True},
        'google': {'available': True},
        'fal': {'available': True},
        'openai': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider == 'recraft'
    assert decision.model == 'recraft-v4-pro'


def test_brand_fidelity_4k_prefers_recraft_over_nano_banana_pro():
    """4K + brand_fidelity='exact' deliberately routes to Recraft despite
    Nano Banana Pro 4K being half the cost ($0.24 vs $0.50). Brand fidelity
    is the trade-off the speaker has explicitly opted into."""
    from src import image_router

    slide = {
        'slide_number': 2,
        'visual_type': 'hero_image',
        'resolution': '4K',
        'brand_fidelity': 'exact',
    }
    available = {
        'recraft': {'available': True},
        'google': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider == 'recraft'
    assert decision.resolution == '4K'
    assert decision.model == 'recraft-v4-pro'


def test_cloud_dispatch_recognises_recraft_provider():
    """When the deckhand router picks recraft, the cloud plugin must have
    'recraft' registered in _PROVIDERS so generate_cloud_image dispatches."""
    cloud_root = Path(__file__).resolve().parent.parent / 'jack-tar-cloud'
    saved = {k: v for k, v in sys.modules.items() if k == 'src' or k.startswith('src.')}
    for k in saved:
        del sys.modules[k]
    sys.path.insert(0, str(cloud_root))
    try:
        from src.generate_cloud_image import _PROVIDERS
        assert 'recraft' in _PROVIDERS, (
            f"cloud plugin missing 'recraft' provider; only has: {sorted(_PROVIDERS)}"
        )
        assert callable(_PROVIDERS['recraft'])
    finally:
        sys.path.remove(str(cloud_root))
        for k in [k for k in sys.modules if k == 'src' or k.startswith('src.')]:
            del sys.modules[k]
