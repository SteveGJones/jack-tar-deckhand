"""Drift detection: deckhand router's capability table must not contradict
the cloud plugin's canonical _PROVIDER_MODEL_RESOLUTIONS for any shared model."""
import sys
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
DECKHAND = WORKTREE / 'plugins' / 'jack-tar-deckhand'
CLOUD = WORKTREE / 'plugins' / 'jack-tar-cloud'

# Canonical model IDs that appear in BOTH plugins. Aliases are allowed to
# exist in the deckhand router-only.
_CANONICAL_SHARED = {
    ('openai', 'gpt-image-1.5'),
    ('google', 'imagen-4.0-fast-generate-001'),
    ('google', 'imagen-4.0-generate-001'),
    ('google', 'imagen-4.0-ultra-generate-001'),
    ('google', 'gemini-3.1-flash-image-preview'),
    ('google', 'gemini-3-pro-image-preview'),
    ('fal', 'fal-ai/flux-2-pro'),
    ('fal', 'fal-ai/flux-2-klein'),
    ('fal', 'fal-ai/ideogram/v3'),
}


def _clear_src_modules():
    """Drop any cached 'src' / 'src.*' so a fresh import resolves through the
    sys.path entry we just prepended."""
    for key in list(sys.modules.keys()):
        if key == 'src' or key.startswith('src.'):
            del sys.modules[key]


@pytest.fixture
def deckhand_table():
    _clear_src_modules()
    sys.path.insert(0, str(DECKHAND))
    try:
        from src.image_router import _PROVIDER_MODEL_RESOLUTIONS
        return dict(_PROVIDER_MODEL_RESOLUTIONS)
    finally:
        sys.path.remove(str(DECKHAND))
        _clear_src_modules()


@pytest.fixture
def cloud_table():
    _clear_src_modules()
    sys.path.insert(0, str(CLOUD))
    try:
        from src.provider_discovery import _PROVIDER_MODEL_RESOLUTIONS as cloud_pmr
        return {k: dict(v) for k, v in cloud_pmr.items()}
    finally:
        sys.path.remove(str(CLOUD))
        _clear_src_modules()


@pytest.mark.parametrize('provider,model', sorted(_CANONICAL_SHARED))
def test_canonical_model_capability_matches_cloud(provider, model, deckhand_table, cloud_table):
    """For each canonical model ID present in both plugins, the deckhand
    router's tier list must equal the cloud plugin's tier list."""
    deckhand_tiers = deckhand_table.get((provider, model))
    cloud_provider = cloud_table.get(provider, {})
    cloud_tiers = cloud_provider.get(model)

    assert deckhand_tiers is not None, f"deckhand missing entry for ({provider}, {model})"
    assert cloud_tiers is not None, f"cloud plugin missing entry for ({provider}, {model})"
    assert sorted(deckhand_tiers) == sorted(cloud_tiers), (
        f"Drift detected for ({provider}, {model}): "
        f"deckhand={deckhand_tiers!r}, cloud={cloud_tiers!r}"
    )
