"""End-to-end: a slide with resolution='4K' routes through deckhand router
to Nano Banana Pro and reaches generate_cloud_image with resolution='4K'.

Exercises two layers of the deckhand pipeline introduced by Issue #60 PR B:
  - image_router.route_slide reads slide.resolution and selects gemini-3-pro
  - render_funnel.execute_funnel_stage at cloud_4k threads resolution kwarg
"""
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

# PLUGIN_ROOT is the canonical name conftest._isolate_src_namespace looks for
# to activate per-test src.* cleanup + sys.path prepending.
PLUGIN_ROOT = Path(__file__).resolve().parent.parent / 'jack-tar-deckhand'


# render_funnel imports src.generate_cloud_image at module load time. The
# deckhand plugin's src/ does not vendor that module (it lives in jack-tar-cloud
# and the legacy worktree-root src/). Stub it before importing render_funnel
# in the test that needs it.
def _ensure_generate_cloud_image_stub():
    if 'src.generate_cloud_image' not in sys.modules:
        stub = types.ModuleType('src.generate_cloud_image')

        def _stub_generate_cloud_image(*args, **kwargs):  # pragma: no cover
            raise NotImplementedError(
                'stub — patch src.render_funnel._generate_cloud_raw instead'
            )

        stub.generate_cloud_image = _stub_generate_cloud_image
        sys.modules['src.generate_cloud_image'] = stub


def test_4k_hero_slide_routes_to_nano_banana_pro():
    """A hero slide marked resolution='4K' must route to gemini-3-pro-image-preview."""
    from src import image_router

    slide = {
        'slide_number': 1,
        'visual_type': 'hero_image',
        'resolution': '4K',
    }
    available = {
        'google': {'available': True},
        'fal': {'available': True},
        'openai': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider == 'google'
    assert decision.model == 'gemini-3-pro-image-preview'
    assert decision.resolution == '4K'


def test_2k_hero_slide_excludes_openai_in_routing():
    """A 2K hero must NOT route to OpenAI (which doesn't support 2K)."""
    from src import image_router

    slide = {
        'slide_number': 2,
        'visual_type': 'hero_image',
        'resolution': '2K',
    }
    available = {
        'google': {'available': True},
        'fal': {'available': True},
        'openai': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider != 'openai'
    assert decision.resolution == '2K'


def test_4k_funnel_stage_threads_resolution_to_generate_cloud_image():
    """render_funnel.execute_funnel_stage at cloud_4k must call generate_cloud_image
    with resolution='4K' and the right Pro model."""
    _ensure_generate_cloud_image_stub()
    from src import render_funnel

    fake = mock.Mock(return_value={'file_path': '/tmp/x.png', 'cost_usd': 0.24})
    with tempfile.TemporaryDirectory() as deck_dir:
        render_funnel.init_render_log(deck_dir)
        with mock.patch('src.render_funnel._generate_cloud_raw', fake):
            render_funnel.execute_funnel_stage(
                deck_dir=deck_dir,
                slide_number=1,
                strategy='full_render',
                prompt='a lighthouse at sunset',
                funnel_stage='cloud_4k',
                model='gemini-3-pro-image-preview',
                output_path='/tmp/x.png',
                provider='google',
            )

    call_kwargs = fake.call_args.kwargs
    assert call_kwargs['resolution'] == '4K'
    assert call_kwargs['provider'] == 'google'
    assert call_kwargs['model'] == 'gemini-3-pro-image-preview'
