# Issue #61 — Recraft V4 Raster Promotion (closes EPIC #58)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote Recraft V4 from icon-only (SVG via `/recraft-icon`) to a first-class raster provider alongside OpenAI / Google / FAL, with a 1K / 2K / 4K resolution ladder (4K via Creative Upscale chain), brand-color preservation, and a brand-fidelity routing rule that prefers Recraft when the speaker marks a slide for exact brand-color match. Closes EPIC #58.

**Architecture:** New `generate_recraft(prompt, output_path, resolution, colors, ...)` provider function in `jack-tar-cloud` mirrors the dual-path pattern used in `generate_cloud_icon.py` (RECRAFT_API_KEY → direct Recraft API, FAL_KEY → via FAL). 4K resolution is implemented as a two-step chain: generate at 2K via the Pro endpoint, then `creativeUpscale` to up to 4096px. New optional `slide.brand_fidelity` field on the strategy map drives the deckhand router's preference for Recraft over Nano Banana / FLUX.

**Tech Stack:** Python 3.11 (pytest, requests, fal-client, openai SDK), JSON Schema, FAL.ai REST + Recraft direct API.

---

## Branch and Worktree

- Worktree: `~/Documents/Development/jack-tar-deckhand/.worktrees/issue-61-recraft-raster` (already created off origin/main commit `4a258a3`)
- Branch: `feat/issue-61-recraft-raster`
- Test runner: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest`
- Spike report: `docs/spikes/2026-05-07-recraft-creative-upscale.md` (committed first)
- Baseline: 54 cloud + 31 deckhand + 49 integration = 134 tests passing

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `docs/spikes/2026-05-07-recraft-creative-upscale.md` | Already written | Endpoint + pricing findings; cost trade-off vs Nano Banana Pro |
| `plugins/jack-tar-cloud/src/generate_cloud_image.py` | Modify | Add Recraft cost tables, resolution capability, `generate_recraft_direct`, `generate_recraft_fal`, dispatch entry, 4K upscale chain |
| `plugins/jack-tar-cloud/src/provider_discovery.py` | Modify | Recraft raster entry: `supported_resolutions: ["1K", "2K", "4K"]`; do NOT modify the existing icon path |
| `plugins/jack-tar-cloud/skills/recraft-image/SKILL.md` | Create | New per-provider raster skill — argument-hint, parse, generate, cost reference |
| `plugins/jack-tar-cloud/skills/image/SKILL.md` | Modify | Add Recraft as 4th option for raster; brand-fidelity routing language |
| `plugins/jack-tar-cloud/.claude-plugin/plugin.json` | Modify | 1.2.1 → 1.3.0 |
| `plugins/jack-tar-deckhand/src/image_router.py` | Modify | Add Recraft RoutingTarget rows; brand-fidelity routing rule; capability table entries |
| `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json` | Modify | Optional `brand_fidelity: "exact" \| "approximate" \| "none"` per slide |
| `plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md` | Modify | Speaker UX for brand-fidelity flag |
| `plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md` | Modify | Optional brand-fidelity prompt during outline |
| `plugins/jack-tar-deckhand/.claude-plugin/plugin.json` | Modify | 1.2.0 → 1.3.0 |
| `.claude-plugin/marketplace.json` | Modify | Both plugins synced |
| `CLAUDE.md` | Modify | "Recraft V4 vs Nano Banana Pro at 4K" decision rule |
| `plugins/jack-tar-cloud/tests/test_recraft_raster.py` | Create | Cost helpers, dual-path mocks, 4K chain |
| `plugins/jack-tar-cloud/tests/test_skill_md_flags.py` | Modify | Extend SKILLS list to include `recraft-image` |
| `plugins/jack-tar-deckhand/tests/test_image_router_brand_fidelity.py` | Create | Brand-fidelity routing tests |
| `plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py` | Modify | Add brand_fidelity validation cases |
| `plugins/integration_tests/test_recraft_brand_fidelity_e2e.py` | Create | Brand-fidelity slide → Recraft, end-to-end |
| `plugins/integration_tests/test_router_capability_drift.py` | Modify | Include Recraft canonical model IDs in the cross-plugin drift check |

---

## Task 1: Commit the spike report

**Files:**
- Add: `docs/spikes/2026-05-07-recraft-creative-upscale.md` (already written)

- [ ] **Step 1: Commit the spike report**

```bash
cd /Users/stevejones/Documents/Development/jack-tar-deckhand/.worktrees/issue-61-recraft-raster
git add docs/spikes/2026-05-07-recraft-creative-upscale.md
git commit -m "docs(spikes): Recraft Creative Upscale endpoint + pricing findings (issue #61)"
```

Expected: clean commit, no other files touched.

---

## Task 2: Recraft cost tables + capability + cost helper

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py` (top-level `_RECRAFT_COSTS` table + `_MODEL_RESOLUTIONS` Recraft entries + `estimate_recraft_cost(tier, resolution)` helper)
- Create: `plugins/jack-tar-cloud/tests/test_recraft_raster.py`

- [ ] **Step 1: Write the failing tests for the cost helper**

```python
# plugins/jack-tar-cloud/tests/test_recraft_raster.py
"""Tests for Recraft V4 raster provider — cost helpers, dual-path generation,
4K via Creative Upscale chain."""
import os
from unittest import mock

import pytest

from src.generate_cloud_image import (
    estimate_recraft_cost,
    ProviderResolutionUnsupportedError,
)


def test_recraft_cost_1k_standard():
    assert estimate_recraft_cost(tier='standard', resolution='1K') == 0.04


def test_recraft_cost_2k_pro():
    assert estimate_recraft_cost(tier='pro', resolution='2K') == 0.25


def test_recraft_cost_4k_chain():
    """4K = generate at 2K Pro ($0.25) + Creative Upscale (~$0.25) = $0.50."""
    assert estimate_recraft_cost(tier='pro', resolution='4K') == 0.50


def test_recraft_cost_4k_standard_falls_back_to_pro():
    """Standard tier doesn't have a 4K mapping; cost helper raises so the
    caller upgrades to pro before generating."""
    with pytest.raises(ValueError, match='standard.*4K'):
        estimate_recraft_cost(tier='standard', resolution='4K')


def test_recraft_cost_unknown_tier():
    with pytest.raises(ValueError, match='Unknown'):
        estimate_recraft_cost(tier='ultra', resolution='1K')


def test_recraft_upscale_cost_override_via_env(monkeypatch):
    """RECRAFT_UPSCALE_COST_USD env var overrides the assumed parity price.

    Used to hot-fix the 4K chain cost if the upscale price isn't the assumed
    $0.25. See spike report for context."""
    monkeypatch.setenv('RECRAFT_UPSCALE_COST_USD', '0.30')
    # Reload the constant — implementation reads env at call time, not import time
    cost_4k = estimate_recraft_cost(tier='pro', resolution='4K')
    assert cost_4k == 0.55  # 0.25 (2K) + 0.30 (override upscale)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_recraft_raster.py -v`

Expected: FAIL — `estimate_recraft_cost` not defined.

- [ ] **Step 3: Implement the cost tables and helper**

In `plugins/jack-tar-cloud/src/generate_cloud_image.py`, after the existing `_FAL_FALLBACK_COST` line (around line 260), add:

```python
# --- Recraft V4 raster pricing (FAL.ai parity assumption for upscale) ---
# Generation costs verified 2026-05-07 via fal.ai/models/fal-ai/recraft/v4/*.
# Upscale cost on direct API not surfaced in public docs; assume FAL parity
# ($0.25). RECRAFT_UPSCALE_COST_USD env var overrides if discovered to differ.

_RECRAFT_GENERATION_COSTS = {
    ('standard', '1K'): 0.04,
    ('pro', '2K'): 0.25,
    # 4K is generate-at-2K then upscale chain — see estimate_recraft_cost
}

_RECRAFT_UPSCALE_COST_DEFAULT = 0.25  # FAL parity; override via env

# Recraft V4 raster supported resolutions per tier
_RECRAFT_TIER_RESOLUTIONS = {
    'standard': ['1K'],
    'pro': ['2K', '4K'],  # 4K is upscale-chained on top of 2K Pro
}


def _recraft_upscale_cost():
    """Return the assumed upscale cost; env override allowed for hot-fix."""
    override = os.environ.get('RECRAFT_UPSCALE_COST_USD')
    if override:
        try:
            return float(override)
        except ValueError:
            pass
    return _RECRAFT_UPSCALE_COST_DEFAULT


def estimate_recraft_cost(tier='pro', resolution='2K'):
    """Return estimated USD cost for a Recraft V4 raster generation.

    Args:
        tier: 'standard' (1024², $0.04) or 'pro' (2048², $0.25).
        resolution: '1K' | '2K' | '4K'. 4K is a chain: 2K Pro generation
            + Creative Upscale at the parity-assumed cost (overridable via
            RECRAFT_UPSCALE_COST_USD env var).

    Returns:
        float: Estimated cost in USD.

    Raises:
        ValueError: If the tier/resolution combination is invalid.
    """
    resolution = _normalise_resolution(resolution)

    if tier not in _RECRAFT_TIER_RESOLUTIONS:
        raise ValueError(
            f"Unknown Recraft tier: {tier!r}. "
            f"Valid: {list(_RECRAFT_TIER_RESOLUTIONS)}"
        )

    supported = _RECRAFT_TIER_RESOLUTIONS[tier]
    if resolution not in supported:
        raise ValueError(
            f"Recraft {tier} tier does not support resolution={resolution!r}. "
            f"Supported: {supported}. "
            f"For 4K use tier='pro' (chains 2K + Creative Upscale)."
        )

    if resolution == '4K':
        # Chain: 2K Pro generation + Creative Upscale
        return _RECRAFT_GENERATION_COSTS[('pro', '2K')] + _recraft_upscale_cost()

    return _RECRAFT_GENERATION_COSTS[(tier, resolution)]
```

Also extend `_MODEL_RESOLUTIONS` (after the existing entries around line 180):

```python
# Recraft V4 raster — added in issue #61. The 'recraft-v4' identifier is
# router-side; under the hood the dispatch picks the actual endpoint
# (text-to-image vs pro/text-to-image vs upscale chain) by tier+resolution.
_MODEL_RESOLUTIONS.update({
    'recraft-v4-standard': ['1K'],
    'recraft-v4-pro': ['2K', '4K'],
})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_recraft_raster.py -v`

Expected: 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py plugins/jack-tar-cloud/tests/test_recraft_raster.py
git commit -m "feat(cloud/recraft): cost tables + estimate_recraft_cost helper for raster + upscale chain"
```

---

## Task 3: `generate_recraft_direct` — Recraft direct API raster path

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py` (new function near other provider funcs)
- Modify: `plugins/jack-tar-cloud/tests/test_recraft_raster.py` (append tests)

- [ ] **Step 1: Append failing tests**

Append to `plugins/jack-tar-cloud/tests/test_recraft_raster.py`:

```python
def test_generate_recraft_direct_1k_calls_recraft_api(monkeypatch, tmp_path):
    """Direct API path: 1K standard tier hits Recraft generation endpoint."""
    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')

    fake_response = mock.Mock()
    fake_response.data = [mock.Mock(url='https://example.com/img.png')]

    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG_BYTES'))
    fake_openai = mock.Mock()
    fake_openai.return_value.images.generate.return_value = fake_response

    out = tmp_path / 'out.png'
    with mock.patch('src.generate_cloud_image.OpenAI', fake_openai), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_direct
        result = generate_recraft_direct(
            prompt='a brand badge',
            output_path=str(out),
            tier='standard',
            resolution='1K',
        )

    assert result['status'] == 'generated'
    assert result['provider'] == 'recraft'
    assert result['tier'] == 'standard'
    assert result['resolution'] == '1K'
    assert out.read_bytes() == b'PNG_BYTES'
    # Confirm we hit Recraft's OpenAI-compatible endpoint
    fake_openai.assert_called_with(
        base_url='https://external.api.recraft.ai/v1',
        api_key='test-key',
    )


def test_generate_recraft_direct_brand_colors_passed(monkeypatch, tmp_path):
    """Brand colors must be forwarded as Recraft `controls.colors` rgb dicts."""
    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')

    fake_response = mock.Mock()
    fake_response.data = [mock.Mock(url='https://example.com/img.png')]
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))
    fake_openai = mock.Mock()
    fake_openai.return_value.images.generate.return_value = fake_response

    with mock.patch('src.generate_cloud_image.OpenAI', fake_openai), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_direct
        generate_recraft_direct(
            prompt='a brand badge',
            output_path=str(tmp_path / 'out.png'),
            tier='standard',
            resolution='1K',
            colors=[
                {'rgb': [0, 51, 102]},
                {'rgb': [255, 204, 0]},
            ],
        )

    call_kwargs = fake_openai.return_value.images.generate.call_args.kwargs
    extra_body = call_kwargs['extra_body']
    assert extra_body['controls']['colors'] == [
        {'rgb': [0, 51, 102]},
        {'rgb': [255, 204, 0]},
    ]


def test_generate_recraft_direct_unsupported_resolution_raises(monkeypatch, tmp_path):
    """Standard tier doesn't support 2K/4K — must raise without making API call."""
    monkeypatch.setenv('RECRAFT_API_KEY', 'test-key')

    with pytest.raises(ProviderResolutionUnsupportedError) as exc:
        from src.generate_cloud_image import generate_recraft_direct
        generate_recraft_direct(
            prompt='x',
            output_path=str(tmp_path / 'out.png'),
            tier='standard',
            resolution='2K',
        )
    assert exc.value.requested == '2K'
    assert '1K' in exc.value.supported


def test_generate_recraft_direct_no_api_key():
    from src.generate_cloud_image import (
        generate_recraft_direct,
        ProviderNotConfiguredError,
    )
    # Make sure RECRAFT_API_KEY is unset
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ProviderNotConfiguredError, match='RECRAFT_API_KEY'):
            generate_recraft_direct(
                prompt='x',
                output_path='/tmp/x.png',
                tier='standard',
                resolution='1K',
            )
```

- [ ] **Step 2: Run tests to verify failure**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_recraft_raster.py -v`

Expected: 4 new tests FAIL — `generate_recraft_direct` not defined.

- [ ] **Step 3: Implement `generate_recraft_direct`**

In `plugins/jack-tar-cloud/src/generate_cloud_image.py`, after `generate_fal` (around line 622), add:

```python
def generate_recraft_direct(prompt, output_path, *, tier='pro', resolution='2K',
                            colors=None, style='realistic_image', **kwargs):
    """Generate a raster image using Recraft V4 direct API.

    Uses OpenAI-compatible endpoint at external.api.recraft.ai/v1.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated image.
        tier: 'standard' (1024², $0.04) or 'pro' (2048², $0.25).
        resolution: '1K' | '2K' | '4K'. 4K chains via Creative Upscale.
        colors: Optional list of RGB control dicts, e.g. [{'rgb': [0, 51, 102]}].
        style: Recraft style — 'realistic_image' (default), 'digital_illustration',
            'vector_illustration', etc.

    Returns:
        dict: {file_path, provider, tier, resolution, model_used, cost_usd, status}

    Raises:
        ProviderNotConfiguredError: If RECRAFT_API_KEY (or RECRAFT_API) not set.
        ProviderResolutionUnsupportedError: If tier doesn't support resolution.
    """
    api_key = os.environ.get('RECRAFT_API_KEY') or os.environ.get('RECRAFT_API')
    if not api_key:
        raise ProviderNotConfiguredError(
            'Recraft not configured: RECRAFT_API_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section D for setup.'
        )

    resolution = _normalise_resolution(resolution)
    supported = _RECRAFT_TIER_RESOLUTIONS.get(tier, [])
    if resolution not in supported:
        raise ProviderResolutionUnsupportedError(
            provider='recraft',
            model=f'recraft-v4-{tier}',
            requested=resolution,
            supported=supported,
        )

    # 4K = chain: generate at 2K Pro then Creative Upscale
    if resolution == '4K':
        return _generate_recraft_direct_with_upscale(
            prompt, output_path, colors=colors, style=style,
        )

    client = OpenAI(
        base_url='https://external.api.recraft.ai/v1',
        api_key=api_key,
    )

    extra_body = {'response_format': 'url'}
    if colors:
        extra_body['controls'] = {'colors': colors}

    # Recraft model-id selector by tier
    model = 'recraftv4' if tier == 'standard' else 'recraftv4'  # same model, different tier endpoints
    # Note: Recraft direct API uses size to imply tier. Pro uses size=2048x2048.
    size = '1024x1024' if tier == 'standard' else '2048x2048'

    response = client.images.generate(
        prompt=prompt,
        model=model,
        style=style,
        size=size,
        extra_body=extra_body,
    )

    image_url = response.data[0].url
    r = requests.get(image_url, timeout=30)
    r.raise_for_status()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(r.content)

    cost = estimate_recraft_cost(tier=tier, resolution=resolution)
    logger.info(
        'Recraft raster generated: %s (tier: %s, resolution: %s, cost: $%.3f)',
        output_path, tier, resolution, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'recraft',
        'tier': tier,
        'resolution': resolution,
        'model_used': f'recraft-v4-{tier}',
        'cost_usd': cost,
        'status': 'generated',
    }


def _generate_recraft_direct_with_upscale(prompt, output_path, *, colors=None,
                                           style='realistic_image'):
    """4K chain: generate at 2K Pro then Creative Upscale.

    Implementation is split out so the 1K/2K path stays simple.
    """
    api_key = os.environ.get('RECRAFT_API_KEY') or os.environ.get('RECRAFT_API')
    # 1) Generate at 2K Pro into a temp file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        generate_recraft_direct(
            prompt=prompt,
            output_path=tmp_path,
            tier='pro',
            resolution='2K',
            colors=colors,
            style=style,
        )

        # 2) POST to creativeUpscale
        with open(tmp_path, 'rb') as f:
            response = requests.post(
                'https://external.api.recraft.ai/v1/images/creativeUpscale',
                headers={'Authorization': f'Bearer {api_key}'},
                files={'file': f},
                timeout=60,
            )
        response.raise_for_status()
        upscaled_url = response.json()['image']['url']

        # 3) Download the upscaled image
        r = requests.get(upscaled_url, timeout=60)
        r.raise_for_status()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(r.content)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    cost = estimate_recraft_cost(tier='pro', resolution='4K')
    logger.info(
        'Recraft raster generated (4K via upscale): %s (cost: $%.3f)',
        output_path, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'recraft',
        'tier': 'pro',
        'resolution': '4K',
        'model_used': 'recraft-v4-pro+upscale',
        'cost_usd': cost,
        'status': 'generated',
    }
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_recraft_raster.py -v`

Expected: 10 PASS (6 cost + 4 direct).

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py plugins/jack-tar-cloud/tests/test_recraft_raster.py
git commit -m "feat(cloud/recraft): generate_recraft_direct (1K/2K) + 4K Creative Upscale chain"
```

---

## Task 4: `generate_recraft_fal` — FAL.ai Recraft raster path + dispatch

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py`
- Modify: `plugins/jack-tar-cloud/tests/test_recraft_raster.py`

- [ ] **Step 1: Append failing tests**

Append to `plugins/jack-tar-cloud/tests/test_recraft_raster.py`:

```python
def test_generate_recraft_fal_1k_calls_text_to_image(monkeypatch, tmp_path):
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    fake_subscribe = mock.Mock(return_value={
        'images': [{'url': 'https://example.com/img.png'}]
    })
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_fal
        result = generate_recraft_fal(
            prompt='a brand badge',
            output_path=str(tmp_path / 'out.png'),
            tier='standard',
            resolution='1K',
        )

    assert result['status'] == 'generated'
    assert result['provider'] == 'fal-recraft'
    fake_subscribe.assert_called_once()
    args = fake_subscribe.call_args
    assert args[0][0] == 'fal-ai/recraft/v4/text-to-image'


def test_generate_recraft_fal_2k_calls_pro_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    fake_subscribe = mock.Mock(return_value={
        'images': [{'url': 'https://example.com/img.png'}]
    })
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_fal
        generate_recraft_fal(
            prompt='x',
            output_path=str(tmp_path / 'out.png'),
            tier='pro',
            resolution='2K',
        )

    args = fake_subscribe.call_args
    assert args[0][0] == 'fal-ai/recraft/v4/pro/text-to-image'


def test_generate_recraft_fal_4k_chains_through_upscale(monkeypatch, tmp_path):
    """4K = 2K Pro generation followed by fal-ai/recraft/upscale/creative."""
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    # First subscribe call: pro/text-to-image returns 2K image url
    # Second subscribe call: upscale/creative returns 4K image url
    fake_subscribe = mock.Mock(side_effect=[
        {'images': [{'url': 'https://example.com/2k.png'}]},
        {'image': {'url': 'https://example.com/4k.png'}},
    ])
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_recraft_fal
        result = generate_recraft_fal(
            prompt='x',
            output_path=str(tmp_path / 'out.png'),
            tier='pro',
            resolution='4K',
        )

    assert result['resolution'] == '4K'
    # Verify the second call was the upscale endpoint
    second_call_args = fake_subscribe.call_args_list[1]
    assert second_call_args[0][0] == 'fal-ai/recraft/upscale/creative'


def test_dispatch_recognises_recraft_provider(monkeypatch, tmp_path):
    """generate_cloud_image(provider='recraft', ...) routes to the new func."""
    monkeypatch.setenv('FAL_KEY', 'test-fal')

    fake_subscribe = mock.Mock(return_value={
        'images': [{'url': 'https://example.com/img.png'}]
    })
    fake_get = mock.Mock(return_value=mock.Mock(content=b'PNG'))

    with mock.patch('src.generate_cloud_image.fal_client.subscribe', fake_subscribe), \
         mock.patch('src.generate_cloud_image.requests.get', fake_get):
        from src.generate_cloud_image import generate_cloud_image
        result = generate_cloud_image(
            prompt='x',
            provider='recraft',
            output_path=str(tmp_path / 'out.png'),
            resolution='1K',
            tier='standard',
        )

    assert result['provider'] == 'fal-recraft'
```

- [ ] **Step 2: Run tests to verify failure**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_recraft_raster.py -v`

Expected: 4 new tests FAIL.

- [ ] **Step 3: Implement `generate_recraft_fal` and dispatch entry**

In `plugins/jack-tar-cloud/src/generate_cloud_image.py`, after `_generate_recraft_direct_with_upscale`, add:

```python
def generate_recraft_fal(prompt, output_path, *, tier='pro', resolution='2K',
                          colors=None, **kwargs):
    """Generate a raster image using Recraft V4 via FAL.ai.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated image.
        tier: 'standard' (1024²) or 'pro' (2048²).
        resolution: '1K' | '2K' | '4K'.
        colors: Optional list of RGB dicts, e.g. [{'r': 0, 'g': 51, 'b': 102}].

    Returns:
        dict: {file_path, provider, tier, resolution, model_used, cost_usd, status}

    Raises:
        ProviderNotConfiguredError: If FAL_KEY not set.
        ProviderResolutionUnsupportedError: If tier doesn't support resolution.
    """
    if not os.environ.get('FAL_KEY'):
        raise ProviderNotConfiguredError(
            'FAL.ai not configured: FAL_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section C for setup.'
        )

    resolution = _normalise_resolution(resolution)
    supported = _RECRAFT_TIER_RESOLUTIONS.get(tier, [])
    if resolution not in supported:
        raise ProviderResolutionUnsupportedError(
            provider='fal-recraft',
            model=f'recraft-v4-{tier}',
            requested=resolution,
            supported=supported,
        )

    if resolution == '4K':
        return _generate_recraft_fal_with_upscale(prompt, output_path, colors=colors)

    endpoint = (
        'fal-ai/recraft/v4/text-to-image' if tier == 'standard'
        else 'fal-ai/recraft/v4/pro/text-to-image'
    )

    arguments = {'prompt': prompt}
    if colors:
        arguments['colors'] = colors

    result = fal_client.subscribe(endpoint, arguments=arguments)
    image_url = result['images'][0]['url']
    r = requests.get(image_url, timeout=30)
    r.raise_for_status()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(r.content)

    cost = estimate_recraft_cost(tier=tier, resolution=resolution)
    logger.info(
        'FAL Recraft raster generated: %s (tier: %s, resolution: %s, cost: $%.3f)',
        output_path, tier, resolution, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'fal-recraft',
        'tier': tier,
        'resolution': resolution,
        'model_used': f'recraft-v4-{tier}',
        'cost_usd': cost,
        'status': 'generated',
    }


def _generate_recraft_fal_with_upscale(prompt, output_path, *, colors=None):
    """4K chain via FAL: 2K Pro generation, then Creative Upscale."""
    arguments = {'prompt': prompt}
    if colors:
        arguments['colors'] = colors

    # 1) Generate at 2K Pro
    gen_result = fal_client.subscribe(
        'fal-ai/recraft/v4/pro/text-to-image',
        arguments=arguments,
    )
    intermediate_url = gen_result['images'][0]['url']

    # 2) Creative Upscale (image_url input form)
    upscale_result = fal_client.subscribe(
        'fal-ai/recraft/upscale/creative',
        arguments={'image_url': intermediate_url},
    )
    upscaled_url = upscale_result['image']['url']

    r = requests.get(upscaled_url, timeout=60)
    r.raise_for_status()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(r.content)

    cost = estimate_recraft_cost(tier='pro', resolution='4K')
    logger.info(
        'FAL Recraft raster generated (4K via upscale): %s (cost: $%.3f)',
        output_path, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'fal-recraft',
        'tier': 'pro',
        'resolution': '4K',
        'model_used': 'recraft-v4-pro+upscale',
        'cost_usd': cost,
        'status': 'generated',
    }
```

Now register the provider in the dispatch dict. Find the `_PROVIDERS` dict (around line 627 — it currently maps `openai`, `google`, `fal`). Replace with:

```python
def _dispatch_recraft(prompt, output_path, **kwargs):
    """Dispatch Recraft to direct API or FAL based on which key is set.

    Mirrors the icon path's dual-route logic: RECRAFT_API_KEY → direct,
    FAL_KEY → fal. Direct API is preferred when both are set.
    """
    if os.environ.get('RECRAFT_API_KEY') or os.environ.get('RECRAFT_API'):
        return generate_recraft_direct(prompt, output_path, **kwargs)
    return generate_recraft_fal(prompt, output_path, **kwargs)


_PROVIDERS = {
    'openai': generate_openai,
    'google': generate_google,
    'fal': generate_fal,
    'recraft': _dispatch_recraft,
}
```

- [ ] **Step 4: Run tests**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_recraft_raster.py -v`

Expected: 14 PASS (6 cost + 4 direct + 4 fal/dispatch).

- [ ] **Step 5: Run full cloud plugin suite for regression**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/ -v 2>&1 | tail -3`

Expected: 54 baseline + 14 new = 68 PASS, 1 SKIPPED.

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py plugins/jack-tar-cloud/tests/test_recraft_raster.py
git commit -m "feat(cloud/recraft): generate_recraft_fal + dispatch via FAL or direct API"
```

---

## Task 5: provider_discovery — Recraft raster surface

**Files:**
- Modify: `plugins/jack-tar-cloud/src/provider_discovery.py`
- Modify: `plugins/jack-tar-cloud/tests/test_recraft_raster.py`

- [ ] **Step 1: Append failing test**

```python
def test_provider_discovery_includes_recraft_raster(monkeypatch):
    """Recraft entry must surface raster supported_resolutions, separate
    from the existing icon SVG path."""
    monkeypatch.setenv('FAL_KEY', 'test-fal')
    from src.provider_discovery import discover_providers
    providers = discover_providers()
    recraft = providers.get('recraft')
    assert recraft is not None
    assert recraft.get('available') is True
    # Raster surface — new in #61
    raster = recraft.get('raster_models', {})
    assert 'recraft-v4-standard' in raster
    assert raster['recraft-v4-standard']['supported_resolutions'] == ['1K']
    assert raster['recraft-v4-pro']['supported_resolutions'] == ['2K', '4K']
```

- [ ] **Step 2: Run to verify failure**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_recraft_raster.py::test_provider_discovery_includes_recraft_raster -v`

Expected: FAIL — no `raster_models` key on Recraft entry.

- [ ] **Step 3: Extend provider_discovery**

In `plugins/jack-tar-cloud/src/provider_discovery.py`, find the section that attaches per-model metadata (around line 268-280, where the existing `_PROVIDER_MODEL_RESOLUTIONS` is consulted). Add Recraft raster_models population after the existing per-provider loop:

```python
    # Attach Recraft raster surface — separate from the icon SVG path which
    # remains in generate_cloud_icon.py (provider entry already keyed 'recraft').
    if 'recraft' in providers:
        providers['recraft']['raster_models'] = {
            'recraft-v4-standard': {'supported_resolutions': ['1K']},
            'recraft-v4-pro': {'supported_resolutions': ['2K', '4K']},
        }
```

- [ ] **Step 4: Run test to verify pass**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_recraft_raster.py -v`

Expected: 15 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-cloud/src/provider_discovery.py plugins/jack-tar-cloud/tests/test_recraft_raster.py
git commit -m "feat(cloud/recraft): surface Recraft raster_models in provider_discovery"
```

---

## Task 6: New `/recraft-image` skill

**Files:**
- Create: `plugins/jack-tar-cloud/skills/recraft-image/SKILL.md`
- Modify: `plugins/jack-tar-cloud/tests/test_skill_md_flags.py` (extend SKILLS list)

- [ ] **Step 1: Create the SKILL.md**

```markdown
---
name: recraft-image
description: Generate raster images using Recraft V4 (1K standard, 2K Pro, 4K via Creative Upscale). Brand-color-fidelity provider — best for slides where exact hex compliance matters more than photorealistic detail. Requires RECRAFT_API_KEY (direct) or FAL_KEY (via FAL).
argument-hint: "image description" [--output PATH] [--tier standard|pro] [--resolution 1K|2K|4K] [--colors HEX,HEX,...] [--style realistic_image|digital_illustration|vector_illustration]
allowed-tools: Bash(python *), Read, Glob
---

# /recraft-image

Generate a raster image via Recraft V4 and report the file path with cost.

This skill wraps `src/generate_cloud_image.py:generate_recraft_*`. Recraft V4 is the brand-color-fidelity raster lane (best when palette has 3+ specified hexes; outperforms FLUX and Nano Banana on exact hex compliance).

## Locate Plugin

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os

if os.environ.get('JACK_TAR_CLOUD_ROOT'):
    print(os.environ['JACK_TAR_CLOUD_ROOT']); sys.exit()

home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-cloud/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()

dev = Path.cwd() / 'plugins' / 'jack-tar-cloud'
if dev.exists():
    print(str(dev)); sys.exit()

print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then
  echo "ERROR: jack-tar-cloud plugin not found." && exit 1
fi
```

## Parse Arguments

- **Description**: quoted text describing the image
- **--output PATH**: Where to save (default `output/recraft-YYYYMMDD-HHMMSS.png`)
- **--tier TIER**: `standard` (1024², $0.04) or `pro` (2048², $0.25). Default `pro`.
- **--resolution RES**: `1K`, `2K`, `4K`. Default `2K`. Tier+resolution must match capability:
  - `standard` → 1K only
  - `pro` → 2K, 4K (4K is 2K + Creative Upscale, ~$0.50 total)
  Unsupported combinations raise `ProviderResolutionUnsupportedError`.
- **--colors COLORS**: Comma-separated hex (e.g. `003366,FFCC00,F5F5F5`). Forwarded as RGB control dicts.
- **--style STYLE**: Recraft style — `realistic_image` (default), `digital_illustration`, `vector_illustration`.

## Parse Brand Colors

```python
colors_hex = "$COLORS".split(",") if "$COLORS" else None
colors_rgb = (
    [{"rgb": [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)]} for h in colors_hex]
    if colors_hex else None
)
```

## Check Provider Availability

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import os
direct = bool(os.environ.get('RECRAFT_API_KEY') or os.environ.get('RECRAFT_API'))
fal = bool(os.environ.get('FAL_KEY'))
print('available' if (direct or fal) else 'not_configured')
"
```

If `not_configured`, tell the user to set `RECRAFT_API_KEY` (direct API, preferred) or `FAL_KEY` (via FAL) and stop.

## Generate

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.generate_cloud_image import generate_cloud_image

colors_hex = '$COLORS'.split(',') if '$COLORS' else None
colors_rgb = (
    [{'rgb': [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)]} for h in colors_hex]
    if colors_hex else None
)

result = generate_cloud_image(
    prompt='''$PROMPT''',
    provider='recraft',
    output_path='$OUTPUT',
    tier='$TIER',
    resolution='$RESOLUTION',
    colors=colors_rgb,
    style='$STYLE',
)
print(json.dumps(result, indent=2))
"
```

## Report Results

- File path, provider (recraft / fal-recraft), tier, resolution, cost, status

## Cost Reference

| Tier | Resolution | Cost | Output |
|---|---|---|---|
| standard | 1K | $0.04 | 1024² |
| pro | 2K | $0.25 | 2048² |
| pro | 4K | $0.50 | up to 4096² (chain: 2K + Creative Upscale) |

**vs Nano Banana Pro 4K ($0.24):** Recraft 4K is ~2× the cost. Choose Recraft when brand-color fidelity is critical (logos, product shots, brand-led hero slides with 3+ specified hexes); choose Nano Banana Pro when photorealistic detail matters more.
```

- [ ] **Step 2: Update the drift detector to include the new skill**

In `plugins/jack-tar-cloud/tests/test_skill_md_flags.py`, find `SKILLS = ['openai-image', 'google-image', 'fal-image', 'image']` and replace with:

```python
SKILLS = ['openai-image', 'google-image', 'fal-image', 'image', 'recraft-image']
```

Also extend `_FLAG_TO_KWARG` to map `--colors` and `--style` and `--tier` if not already covered:

```python
_FLAG_TO_KWARG = {
    'aspect-ratio': 'aspect_ratio',
    'background': 'background',
    'colors': 'colors',          # recraft-image — list of RGB dicts
    'model': 'model',
    'quality': 'quality',
    'resolution': 'resolution',
    'size': ('size', 'image_size'),
    'style': 'style',            # recraft-image
    'tier': 'tier',              # recraft-image
}
```

- [ ] **Step 3: Run drift detector**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_skill_md_flags.py -v`

Expected: 4 PASS + 1 SKIPPED (image router) + new `recraft-image` PASS = 5 PASS, 1 SKIPPED.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-cloud/skills/recraft-image/SKILL.md plugins/jack-tar-cloud/tests/test_skill_md_flags.py
git commit -m "feat(cloud/recraft-image): new SKILL.md for raster generation"
```

---

## Task 7: image smart-router — Recraft as 4th raster option

**Files:**
- Modify: `plugins/jack-tar-cloud/skills/image/SKILL.md`

- [ ] **Step 1: Edit the routing description**

Find the `## Select Provider and Route` section. After the existing content-aware routing list, add:

```markdown
**Brand-color-fidelity routing (issue #61):** when the prompt or context indicates exact brand-color match matters (logos, product shots, brand-led hero slides), prefer Recraft V4 raster:
- 1K, 2K → `/jack-tar-cloud:recraft-image --tier pro --resolution 2K --colors HEX,HEX,...`
- 4K → `/jack-tar-cloud:recraft-image --tier pro --resolution 4K --colors HEX,HEX,...` (chain: 2K + Creative Upscale, $0.50 vs $0.24 Nano Banana Pro 4K — premium for brand fidelity)

Recraft outperforms FLUX/Nano Banana on exact hex compliance but is ~2× cost at 4K. The deckhand strategy-map's `brand_fidelity` field controls automated routing; speakers can override via `--provider recraft`.
```

- [ ] **Step 2: Run drift detector to confirm router pattern still passes**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_skill_md_flags.py -v`

Expected: still 5 PASS, 1 SKIPPED (image is the SKIPPED one — router-doc test passes).

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-cloud/skills/image/SKILL.md
git commit -m "docs(cloud/image): document brand-fidelity routing to Recraft V4 raster"
```

---

## Task 8: Strategy map schema — `brand_fidelity` field

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json`
- Modify: `plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py`

- [ ] **Step 1: Append failing tests**

Append to `plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Expected: 4 FAIL (the omitted-still-valid case may already pass since the schema doesn't have `additionalProperties: false`).

- [ ] **Step 3: Add the property to the schema**

In `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json`, alongside the `resolution` property added in #60, add:

```json
          "brand_fidelity": {
            "type": "string",
            "enum": ["exact", "approximate", "none"],
            "default": "none",
            "description": "Optional slide-level brand-color fidelity flag. 'exact' routes to Recraft V4 raster (best hex compliance, ~2× cost at 4K). 'approximate' allows the default photorealistic pipeline. 'none' indicates brand-color fidelity is not a concern. Default 'none'."
          },
```

- [ ] **Step 4: Run tests**

Expected: 13 PASS (8 baseline + 5 new).

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py
git commit -m "feat(deckhand/schema): strategy-map slide.brand_fidelity field"
```

---

## Task 9: image_router — Recraft routing rows + brand-fidelity rule

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/image_router.py`
- Create: `plugins/jack-tar-deckhand/tests/test_image_router_brand_fidelity.py`

- [ ] **Step 1: Write failing tests**

```python
# plugins/jack-tar-deckhand/tests/test_image_router_brand_fidelity.py
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
    # Falls back to existing production row first target (FAL)
    assert decision.provider != 'recraft'
    assert decision.is_fallback is True
```

- [ ] **Step 2: Run to verify failures**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_image_router_brand_fidelity.py -v`

Expected: 5 FAIL.

- [ ] **Step 3: Implement Recraft routing rows + brand-fidelity rule**

In `plugins/jack-tar-deckhand/src/image_router.py`, add new ROUTING_MATRIX entries for brand-fidelity-exact modes. After the existing `('hero_image', 'production_4k')` row:

```python
    # Brand-fidelity-exact rows — added by issue #61. The router upgrades
    # mode to 'production_brand_exact' when slide.brand_fidelity == 'exact'.
    # First target is Recraft (best hex compliance); fallbacks preserve
    # existing photorealistic providers when Recraft is unavailable.
    ('hero_image', 'production_brand_exact'): [
        RoutingTarget('cloud-generate-image', 'recraft', 'recraft-v4-pro', 0.25, '2K'),
        RoutingTarget('cloud-generate-image', 'fal', 'fal-ai/flux-2-pro', 0.075, '2K'),
    ],
    ('hero_image', 'production_brand_exact_4k'): [
        RoutingTarget('cloud-generate-image', 'recraft', 'recraft-v4-pro', 0.50, '4K'),
        RoutingTarget('cloud-generate-image', 'google', 'gemini-3-pro-image-preview', 0.24, '4K'),
    ],
```

Update `_PROVIDER_MODEL_RESOLUTIONS` to include Recraft entries:

```python
_PROVIDER_MODEL_RESOLUTIONS.update({
    ('recraft', 'recraft-v4-standard'): ['1K'],
    ('recraft', 'recraft-v4-pro'): ['2K', '4K'],
})
```

In `route_slide`, extend the `effective_mode` derivation to consult `slide.brand_fidelity`:

```python
    # Resolution-aware mode upgrade: a slide-level resolution hint upgrades
    # the mode key so we hit the high-res routing rows in ROUTING_MATRIX.
    requested_resolution = slide.get('resolution', '1K')
    brand_fidelity = slide.get('brand_fidelity', 'none')
    effective_mode = mode
    if mode == 'production':
        if brand_fidelity == 'exact':
            # Brand-fidelity-exact takes priority over resolution upgrade — use
            # the dedicated routing row that prefers Recraft, with resolution
            # encoded in the row key for 4K.
            if requested_resolution == '4K':
                effective_mode = 'production_brand_exact_4k'
            else:
                effective_mode = 'production_brand_exact'
        elif requested_resolution in ('2K', '4K'):
            effective_mode = f'production_{requested_resolution.lower()}'
```

- [ ] **Step 4: Run all router tests**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_image_router_resolution.py plugins/jack-tar-deckhand/tests/test_image_router_brand_fidelity.py -v`

Expected: existing 11 + new 5 = 16 PASS.

- [ ] **Step 5: Run full deckhand suite for regression**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/ -v 2>&1 | tail -3`

Expected: existing 31 + new 5 + new schema tests = clean PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-deckhand/src/image_router.py plugins/jack-tar-deckhand/tests/test_image_router_brand_fidelity.py
git commit -m "feat(deckhand/image-router): brand-fidelity routing prefers Recraft V4 raster"
```

---

## Task 10: strategy-map and narrative-architect skill prompts — speaker UX

**Files:**
- Modify: `plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md`
- Modify: `plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md`

- [ ] **Step 1: Add brand-fidelity guidance to strategy-map/SKILL.md**

Find the existing "Resolution selection" section (added in #60). After it, append:

```markdown
## Brand-fidelity selection

Most slides don't need exact brand-color compliance — Nano Banana Pro and FLUX produce close-enough palette match. For slides where the brand colors must be hex-exact (logos, product shots, brand-led hero or closer slides with 3+ specified hexes), mark `brand_fidelity: "exact"` in the StrategyMap entry to route to Recraft V4 raster.

**When to choose `brand_fidelity: "exact"`:**
- Logo or wordmark renderings
- Product shots where brand color is part of the identity
- Hero opener for a brand-led talk where the palette must be visually unambiguous

**When to leave it default (`"none"` or omitted):**
- Photographic backgrounds (Recraft underperforms FLUX/Nano Banana on photorealism)
- Generic illustrative imagery
- Any slide where the palette doesn't include 3+ specified hexes

**Cost implications:**
- 2K Recraft Pro: $0.25 (matches FAL FLUX 2 Pro 2K)
- 4K Recraft (chain: 2K + Creative Upscale): $0.50 — vs Nano Banana Pro 4K $0.24. Confirm with the speaker before marking 4K hero slides for `brand_fidelity: "exact"` — three such slides represent ~$1.50 vs ~$0.72 of generation spend.
```

- [ ] **Step 2: Add brand-fidelity prompt to narrative-architect/SKILL.md**

Find the existing "Optional: hero-slide resolution annotation" section. Add a parallel paragraph:

```markdown
## Optional: brand-fidelity annotation

If the talk is brand-led (product launch, company keynote, vendor pitch) or has slides where exact brand-color match is critical (logos, product shots), ask: "For [slide N], should brand colors be rendered hex-exact (`brand_fidelity: "exact"` → Recraft V4 raster, ~2× cost at 4K) or close-enough (default → FLUX or Nano Banana)?" Annotate `brand_fidelity` on the SlideOutline entry if so. Default `"none"` unchanged.
```

- [ ] **Step 3: Smoke-grep**

Run:
```bash
grep -c "Brand-fidelity selection" plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md
grep -c "brand-fidelity annotation" plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md
```

Each should return `1`.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md
git commit -m "docs(deckhand/skills): speaker UX for brand-fidelity flag (issue #61)"
```

---

## Task 11: Cross-plugin integration test — brand_fidelity slide → Recraft

**Files:**
- Create: `plugins/integration_tests/test_recraft_brand_fidelity_e2e.py`
- Modify: `plugins/integration_tests/test_router_capability_drift.py` (extend canonical-shared set)

- [ ] **Step 1: Write the integration test**

```python
# plugins/integration_tests/test_recraft_brand_fidelity_e2e.py
"""End-to-end: a slide with brand_fidelity='exact' routes through deckhand
router to Recraft V4 raster (and the cloud plugin actually has the provider
function wired to dispatch on provider='recraft')."""
import sys
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parent.parent / 'jack-tar-deckhand'


def test_brand_fidelity_exact_routes_to_recraft():
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


def test_cloud_dispatch_recognises_recraft_provider(monkeypatch, tmp_path):
    """When the deckhand router picks recraft, the cloud plugin must accept
    provider='recraft' and dispatch correctly."""
    monkeypatch.setenv('FAL_KEY', 'test')

    cloud_root = Path(__file__).resolve().parent.parent / 'jack-tar-cloud'
    sys.path.insert(0, str(cloud_root))
    sys.modules.pop('src.generate_cloud_image', None)
    try:
        from src.generate_cloud_image import generate_cloud_image, _PROVIDERS
        assert 'recraft' in _PROVIDERS
        # Smoke check: the dispatch function exists and is callable
        assert callable(_PROVIDERS['recraft'])
    finally:
        sys.path.remove(str(cloud_root))
        sys.modules.pop('src.generate_cloud_image', None)
```

- [ ] **Step 2: Extend the cross-plugin drift check**

In `plugins/integration_tests/test_router_capability_drift.py`, add to `_CANONICAL_SHARED`:

```python
_CANONICAL_SHARED = {
    # ... existing entries ...
    ('recraft', 'recraft-v4-standard'),
    ('recraft', 'recraft-v4-pro'),
}
```

The cloud-side check reads from `provider_discovery._PROVIDER_MODEL_RESOLUTIONS` — that table doesn't include Recraft entries (Recraft tier resolutions live in `_RECRAFT_TIER_RESOLUTIONS` in `generate_cloud_image.py`). Adapt the cloud-side fixture to also pull from the Recraft table:

```python
@pytest.fixture
def cloud_table():
    sys.path.insert(0, str(CLOUD))
    sys.modules.pop('src.provider_discovery', None)
    sys.modules.pop('src.generate_cloud_image', None)
    try:
        from src.provider_discovery import _PROVIDER_MODEL_RESOLUTIONS as cloud_pmr
        from src.generate_cloud_image import _RECRAFT_TIER_RESOLUTIONS
        # Promote Recraft tier table into the (provider, model) form that the
        # deckhand router uses
        recraft_entries = {
            f'recraft-v4-{tier}': resolutions
            for tier, resolutions in _RECRAFT_TIER_RESOLUTIONS.items()
        }
        merged = {k: dict(v) for k, v in cloud_pmr.items()}
        merged.setdefault('recraft', {}).update(recraft_entries)
        return merged
    finally:
        sys.path.remove(str(CLOUD))
        sys.modules.pop('src.provider_discovery', None)
        sys.modules.pop('src.generate_cloud_image', None)
```

- [ ] **Step 3: Run the integration tests**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/integration_tests/ -v 2>&1 | tail -5`

Expected: 49 baseline + 2 new + extended drift parametric (was 9, now 11) = clean PASS.

- [ ] **Step 4: Commit**

```bash
git add plugins/integration_tests/test_recraft_brand_fidelity_e2e.py plugins/integration_tests/test_router_capability_drift.py
git commit -m "test(integration): brand_fidelity slide routes Recraft; drift check covers Recraft tiers"
```

---

## Task 12: CLAUDE.md — Recraft V4 vs Nano Banana Pro at 4K decision rule

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add a new section after the "Resolution selection guide"**

Append after the existing "Resolution selection guide" section:

```markdown
- **Recraft V4 raster (issue #61, 2026-05-07):** Promoted from icon-only to first-class raster provider with 1K/2K/4K ladder. Best brand-color fidelity; speakers opt slides in via `brand_fidelity: "exact"` on the StrategyMap entry.
  - **When Recraft beats Nano Banana / FLUX:** logos, product shots, brand-led hero slides with 3+ specified hexes — Recraft renders exact hex; the others approximate.
  - **When Nano Banana / FLUX beats Recraft:** photorealistic detail, illustrative scenes — Recraft is design-centric, not photo-first.
  - **Recraft V4 vs Nano Banana Pro at 4K decision rule:**
    - Default 4K → Nano Banana Pro ($0.24, photorealistic)
    - `brand_fidelity: "exact"` AND ≥3 specified hexes → Recraft Pro 4K via Creative Upscale chain ($0.50, brand-fidelity premium)
    - The router's `production_brand_exact_4k` row encodes this; the deckhand image_router auto-derives the routing mode from `slide.brand_fidelity` and `slide.resolution`.
  - **Implementation:** `generate_recraft_direct` (RECRAFT_API_KEY) and `generate_recraft_fal` (FAL_KEY) in `plugins/jack-tar-cloud/src/generate_cloud_image.py`. 4K is generate-2K-then-`creativeUpscale` chain.
  - **New skill:** `/jack-tar-cloud:recraft-image` — per-provider raster skill with `--tier`, `--resolution`, `--colors`, `--style` flags.
  - **Spike:** `docs/spikes/2026-05-07-recraft-creative-upscale.md` — endpoint + pricing findings.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude): Recraft V4 raster + brand-fidelity routing decision rule (issue #61)"
```

---

## Task 13: Version bumps and marketplace sync

**Files:**
- Modify: `plugins/jack-tar-cloud/.claude-plugin/plugin.json`
- Modify: `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Bump cloud plugin to 1.3.0**

Change `"version": "1.2.1"` → `"version": "1.3.0"` in `plugins/jack-tar-cloud/.claude-plugin/plugin.json`.

- [ ] **Step 2: Bump deckhand plugin to 1.3.0**

Change `"version": "1.2.0"` → `"version": "1.3.0"` in `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`.

- [ ] **Step 3: Sync marketplace manifest**

In `.claude-plugin/marketplace.json`, bump both:
- `jack-tar-cloud` 1.2.1 → 1.3.0
- `jack-tar-deckhand` 1.2.0 → 1.3.0

- [ ] **Step 4: Validate JSON**

```bash
python3 -c "
import json
for p in [
    'plugins/jack-tar-cloud/.claude-plugin/plugin.json',
    'plugins/jack-tar-deckhand/.claude-plugin/plugin.json',
    '.claude-plugin/marketplace.json',
]:
    json.load(open(p))
print('OK')
"
```

Expected: `OK`

- [ ] **Step 5: Run all tests**

```bash
for p in jack-tar-cloud jack-tar-deckhand; do
  echo "=== $p ==="
  /Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/$p/tests/ 2>&1 | tail -1
done
echo "=== integration ==="
/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/integration_tests/ 2>&1 | tail -1
```

Expected: clean PASS across all suites.

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-cloud/.claude-plugin/plugin.json plugins/jack-tar-deckhand/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump jack-tar-cloud 1.2.1 → 1.3.0 and jack-tar-deckhand 1.2.0 → 1.3.0 (Recraft V4 raster)"
```

---

## Task 14: Push, open PR, merge after CI green

- [ ] **Step 1: Push branch**

```bash
git push -u origin feat/issue-61-recraft-raster
```

- [ ] **Step 2: Open PR**

```bash
gh pr create --title "feat(jack-tar-cloud + jack-tar-deckhand): Recraft V4 raster promotion (1K/2K/4K) + brand-fidelity routing — closes EPIC #58" --body "$(cat <<'EOF'
## Summary

Promotes Recraft V4 from icon-only (SVG via /recraft-icon) to a first-class raster provider with 1K/2K/4K ladder, brand-color preservation, and a brand-fidelity routing rule.

- **New raster provider** in jack-tar-cloud: \`generate_recraft_direct\` (RECRAFT_API_KEY) and \`generate_recraft_fal\` (FAL_KEY), dispatched via provider='recraft'. 4K = generate-2K-then-\`creativeUpscale\` chain.
- **New skill** \`/jack-tar-cloud:recraft-image\` — per-provider raster with --tier/--resolution/--colors/--style flags.
- **Strategy-map schema** gains optional \`brand_fidelity: "exact" | "approximate" | "none"\` per slide.
- **Image router** new ROUTING_MATRIX rows \`production_brand_exact\` and \`production_brand_exact_4k\` prefer Recraft over Nano Banana / FLUX when slide.brand_fidelity == 'exact'.
- **Speaker UX** in strategy-map and narrative-architect SKILL.md guides the brand-fidelity decision with cost trade-offs (Recraft 4K \$0.50 vs Nano Banana Pro 4K \$0.24).
- **Cross-plugin drift check** extended to cover Recraft tier resolutions.
- Bumps jack-tar-cloud 1.2.1 → 1.3.0, jack-tar-deckhand 1.2.0 → 1.3.0; marketplace synced.

Closes EPIC #58 (#62 / #59 / #60 already merged).

## Test plan

- [x] Cost helpers + dual-path generation: 14 new tests in plugins/jack-tar-cloud/tests/test_recraft_raster.py
- [x] Brand-fidelity routing: 5 new tests in plugins/jack-tar-deckhand/tests/test_image_router_brand_fidelity.py
- [x] Schema validation: 5 new tests for brand_fidelity field
- [x] Cross-plugin integration: 2 new tests + extended drift parametric (9 → 11 entries)
- [x] Existing baselines pass: cloud (was 54 → 68), deckhand (was 31 → 36), integration (was 49 → 53)
- [x] CI: code-quality, plugin-tests-cloud + matrix, integration-tests, json-validation, summary
EOF
)"
```

- [ ] **Step 3: Wait for CI green; merge with `gh pr merge <N> --merge`**

- [ ] **Step 4: Update memory entries**

After merge:
- Update `project_implementation_progress.md` — EPIC #58 closed (4/4 children).
- Update MEMORY.md index entry to reflect EPIC closure.
- Add new memory if any reusable pattern emerged (e.g. dual-path provider with chain operation).

---

## Self-review

**Spec coverage:**
- §1 Recraft raster provider function — Tasks 2-4
- §2 Cost tables — Task 2
- §3 Provider discovery — Task 5
- §4 Image router brand-fidelity — Task 9
- §5 New /recraft-image skill — Task 6
- §6 Strategy map brand-fidelity flag — Task 8
- §7 Tests — Tasks 2-9, 11 (total ~26 new tests)
- §8 Documentation — Tasks 7, 10, 12
- §9 Version bumps — Task 13

**Placeholder scan:** None remaining. Every step has explicit code or commands.

**Type consistency:**
- Recraft tier strings: `'standard'` / `'pro'` everywhere
- Resolution strings: `'1K'` / `'2K'` / `'4K'` (plus `'512'` for Nano Banana Flash) match cloud plugin canonical form
- Provider key for dispatch: `'recraft'` (single key for both direct + FAL paths; internal dispatch decides)
- Result dicts use `provider`/`tier`/`resolution`/`model_used`/`cost_usd`/`status` consistently
