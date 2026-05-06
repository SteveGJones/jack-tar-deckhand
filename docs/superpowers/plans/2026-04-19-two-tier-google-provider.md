# Two-Tier Google Provider Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up the two distinct Google image generation tiers (Nanobanana = Gemini models via generate_content API, Imagen = imagen-4 models via generate_images API) through provider discovery, routing matrix, render funnel, and skill files so the pipeline uses real model IDs and selects the right tier for each use case.

**Architecture:** `generate_cloud_image.py` already handles both APIs correctly — no changes needed there. The work is in three upstream Python modules (provider_discovery, image_router, render_funnel) that feed it the right model names, plus four skill markdown files that need updated documentation and provider keys.

**Tech Stack:** Python 3.10+, pytest, namedtuple, existing test fixtures.

---

## File Map

| File | Change | Tests |
|------|--------|-------|
| `src/provider_discovery.py` | Add `tiers` dict to Google discovery result | `tests/test_provider_discovery.py` |
| `src/image_router.py` | Add `tier` field to `RoutingTarget`, replace abstract Google model names with real API IDs, add `recommended_tier` to `UpgradeDecision` | `tests/test_image_router.py` |
| `src/render_funnel.py` | Pass `model` through `_generate_cloud` to `generate_cloud_image` | `tests/test_render_funnel.py` |
| `plugins/jack-tar-cloud/skills/google-image/SKILL.md` | Fix `provider='google_vertex'` → `provider='google'`, add `--model` and `--tier` params | — |
| `plugins/jack-tar-cloud/skills/image/SKILL.md` | Update routing priority for content suitability | — |
| `plugins/jack-tar-cloud/skills/verify/SKILL.md` | Report Google tiers separately | — |
| `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` | Document tier selection in Step 9A | — |

---

## Task 1: Add Google tiers to provider discovery

When `GOOGLE_API_KEY` (or `GOOGLE_APPLICATION_CREDENTIALS`) is set, the Google discovery result should include a `tiers` dict listing all four available models with costs. Both API families use the same credential — if the key is set, all four are available.

**Files:**
- Modify: `src/provider_discovery.py:35-37,181-182`
- Test: `tests/test_provider_discovery.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_provider_discovery.py`:

```python
class TestGoogleTiers:
    """Google provider discovery should report all available tiers."""

    def test_google_tiers_when_available(self):
        from src.provider_discovery import discover_providers
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            result = discover_providers(config_path=None)
        google = result['google']
        assert google['available'] is True
        assert 'tiers' in google
        tiers = google['tiers']
        assert 'nanobanana_flash' in tiers
        assert tiers['nanobanana_flash']['model'] == 'gemini-3.1-flash-image-preview'
        assert tiers['nanobanana_flash']['cost'] == 0.067
        assert 'nanobanana_pro' in tiers
        assert tiers['nanobanana_pro']['model'] == 'gemini-3-pro-image-preview'
        assert tiers['nanobanana_pro']['cost'] == 0.134
        assert 'imagen_fast' in tiers
        assert tiers['imagen_fast']['model'] == 'imagen-4.0-fast-generate-001'
        assert tiers['imagen_fast']['cost'] == 0.020
        assert 'imagen_standard' in tiers
        assert tiers['imagen_standard']['model'] == 'imagen-4.0-generate-001'
        assert tiers['imagen_standard']['cost'] == 0.040

    def test_google_tiers_empty_when_unavailable(self):
        from src.provider_discovery import discover_providers
        env = {k: '' for k in ['GOOGLE_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS',
                                'OPENAI_API_KEY', 'FAL_KEY', 'RECRAFT_API_KEY']}
        with patch.dict(os.environ, env, clear=False):
            # Unset the keys
            for k in env:
                os.environ.pop(k, None)
            result = discover_providers(config_path=None)
        google = result['google']
        assert google['available'] is False
        assert google.get('tiers', {}) == {}

    def test_google_backward_compat_available_and_model_fields(self):
        """Existing code reads google['available'] and google['model'] — keep them."""
        from src.provider_discovery import discover_providers
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            result = discover_providers(config_path=None)
        google = result['google']
        assert google['available'] is True
        assert 'model' in google  # backward compat
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_provider_discovery.py::TestGoogleTiers -v`
Expected: FAIL — `KeyError: 'tiers'` because `discover_providers` doesn't return tiers yet.

- [ ] **Step 3: Write the implementation**

In `src/provider_discovery.py`, add Google tiers constant after line 47:

```python
# Google image generation tiers — both API families use the same credential
_GOOGLE_TIERS = {
    'nanobanana_flash': {'model': 'gemini-3.1-flash-image-preview', 'cost': 0.067},
    'nanobanana_pro': {'model': 'gemini-3-pro-image-preview', 'cost': 0.134},
    'imagen_fast': {'model': 'imagen-4.0-fast-generate-001', 'cost': 0.020},
    'imagen_standard': {'model': 'imagen-4.0-generate-001', 'cost': 0.040},
}
```

Then modify `discover_providers()` (around line 182). After getting `google_result`, add tiers:

```python
    google_vars = _resolve_env_vars('google', config)
    google_result = probe_env_provider(google_vars, 'google', 'imagen-4')
    if google_result['available']:
        google_result['tiers'] = _GOOGLE_TIERS
    else:
        google_result['tiers'] = {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_provider_discovery.py -v`
Expected: ALL pass (existing + new).

- [ ] **Step 5: Commit**

```bash
git add src/provider_discovery.py tests/test_provider_discovery.py
git commit -m "feat: add Google tiers to provider discovery"
```

---

## Task 2: Add tier to RoutingTarget and update Google model IDs

Add a `tier` field to `RoutingTarget` (with default `None` for backward compat). Replace abstract Google model names (`imagen-4-standard`, `imagen-4-fast`) with real API model IDs. Add `recommended_tier` to `UpgradeDecision`.

**Files:**
- Modify: `src/image_router.py:16-21,51-114,369-470`
- Test: `tests/test_image_router.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_image_router.py`:

```python
class TestRoutingTargetTier:
    """RoutingTarget should have a tier field."""

    def test_routing_target_has_tier_field(self):
        from src.image_router import RoutingTarget
        rt = RoutingTarget('cloud-generate-image', 'google', 'gemini-3.1-flash-image-preview', 0.067, 'standard')
        assert rt.tier == 'standard'

    def test_routing_target_tier_defaults_to_none(self):
        from src.image_router import RoutingTarget
        rt = RoutingTarget('ollama-image', 'ollama', 'x/z-image-turbo', 0.00)
        assert rt.tier is None

    def test_google_hero_production_uses_real_model_id(self):
        from src.image_router import ROUTING_MATRIX
        targets = ROUTING_MATRIX[('hero_image', 'production')]
        google_targets = [t for t in targets if t.provider == 'google']
        assert len(google_targets) >= 1
        # Must be a real API model ID, not the abstract 'imagen-4-standard'
        for t in google_targets:
            assert t.model in (
                'gemini-3.1-flash-image-preview',
                'gemini-3-pro-image-preview',
                'imagen-4.0-fast-generate-001',
                'imagen-4.0-generate-001',
            ), f"Google model '{t.model}' is not a real API model ID"

    def test_google_pattern_draft_uses_real_model_id(self):
        from src.image_router import ROUTING_MATRIX
        targets = ROUTING_MATRIX[('pattern_background', 'draft')]
        google_targets = [t for t in targets if t.provider == 'google']
        for t in google_targets:
            assert t.model in (
                'imagen-4.0-fast-generate-001',
                'imagen-4.0-generate-001',
            ), f"Pattern draft Google model '{t.model}' should be Imagen (cheap)"


class TestUpgradeDecisionTier:
    """UpgradeDecision should include recommended_tier."""

    def test_upgrade_decision_has_recommended_tier(self):
        from src.image_router import UpgradeDecision
        ud = UpgradeDecision(
            slide_number=1, image_id='slide-01-hero', action='upgrade',
            reason='test', draft_prompt='test prompt', target_provider='google',
            target_model='gemini-3.1-flash-image-preview', target_size='1536x1024',
            estimated_cost_usd=0.067, warnings=[], recommended_tier='standard',
        )
        assert ud.recommended_tier == 'standard'

    def test_upgrade_decision_tier_defaults_to_none(self):
        from src.image_router import UpgradeDecision
        ud = UpgradeDecision(
            slide_number=1, image_id='slide-01-hero', action='keep',
            reason='test', draft_prompt=None, target_provider=None,
            target_model=None, target_size=None,
            estimated_cost_usd=0.0, warnings=[],
        )
        assert ud.recommended_tier is None

    def test_plan_production_upgrade_includes_tier(self):
        from src.image_router import plan_production_upgrade
        draft_manifest = {
            'images': [{
                'slide_number': 1,
                'image_id': 'slide-01-hero',
                'model_used': 'x/z-image-turbo',
                'source_prompt': 'test prompt',
            }]
        }
        outline = {'slides': [{'slide_number': 1, 'slide_type': 'title'}]}
        providers = {
            'ollama': {'available': False, 'models': []},
            'openai': {'available': False},
            'google': {'available': True, 'model': 'imagen-4', 'tiers': {}},
            'fal': {'available': True, 'models': ['flux-2-pro']},
            'recraft': {'available': False},
        }
        budget = {'budget_state': 'allow', 'remaining_usd': 5.0}
        decisions = plan_production_upgrade(draft_manifest, outline, providers, budget)
        assert len(decisions) == 1
        assert hasattr(decisions[0], 'recommended_tier')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_image_router.py::TestRoutingTargetTier tests/test_image_router.py::TestUpgradeDecisionTier -v`
Expected: FAIL — `TypeError` on RoutingTarget (no tier field) and UpgradeDecision (no recommended_tier field).

- [ ] **Step 3: Add tier to RoutingTarget namedtuple**

In `src/image_router.py`, modify RoutingTarget (lines 16-21):

```python
RoutingTarget = namedtuple('RoutingTarget', [
    'skill',           # skill name: 'ollama-image', 'cloud-generate-image', etc.
    'provider',        # provider key: 'ollama', 'openai', 'google', 'fal', 'recraft', 'local'
    'model',           # model identifier: 'x/z-image-turbo', 'gpt-image-1.5', etc.
    'cost_per_image',  # estimated USD cost
    'tier',            # 'draft', 'standard', 'premium', or None
], defaults=[None])
```

- [ ] **Step 4: Add recommended_tier to UpgradeDecision namedtuple**

In `src/image_router.py`, modify UpgradeDecision (lines 33-44):

```python
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
    'warnings',         # list of warning strings (empty list if none)
    'recommended_tier', # 'draft', 'standard', 'premium', or None
], defaults=[None])
```

- [ ] **Step 5: Update Google model names in ROUTING_MATRIX**

Replace abstract names with real API model IDs. In `src/image_router.py` ROUTING_MATRIX (lines 51-96):

Change these specific entries:

Line 60 (`hero_image`, `production`, Google entry):
```python
RoutingTarget('cloud-generate-image', 'google', 'gemini-3.1-flash-image-preview', 0.067, 'standard'),
```

Line 73 (`pattern_background`, `draft`, Google entry):
```python
RoutingTarget('cloud-generate-image', 'google', 'imagen-4.0-fast-generate-001', 0.02, 'draft'),
```

Line 77 (`pattern_background`, `production`, Google entry):
```python
RoutingTarget('cloud-generate-image', 'google', 'imagen-4.0-fast-generate-001', 0.02, 'draft'),
```

In BUDGET_DEGRADED_MATRIX (line 101):
```python
RoutingTarget('cloud-generate-image', 'google', 'imagen-4.0-fast-generate-001', 0.02, 'draft'),
```

- [ ] **Step 6: Set recommended_tier in plan_production_upgrade**

In `plan_production_upgrade()`, update the upgrade UpgradeDecision construction (around line 457) to include `recommended_tier` from the route:

```python
        decisions.append(UpgradeDecision(
            slide_number=slide_num,
            image_id=image_id,
            action='upgrade',
            reason=f'{visual_type} benefits from cloud quality',
            draft_prompt=draft_prompt,
            target_provider=route.provider,
            target_model=route.model,
            target_size=target_size,
            estimated_cost_usd=route.cost_per_image,
            warnings=warnings,
            recommended_tier=route.tier,
        ))
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_image_router.py -v`
Expected: ALL pass. The `defaults=[None]` on both namedtuples ensures backward compatibility — existing 4-field RoutingTarget and 10-field UpgradeDecision constructors still work.

- [ ] **Step 8: Commit**

```bash
git add src/image_router.py tests/test_image_router.py
git commit -m "feat: add tier to RoutingTarget and real Google model IDs"
```

---

## Task 3: Pass model through render funnel to cloud generator

The `_generate_cloud()` wrapper in `render_funnel.py` currently drops the `model` parameter. For Google, `model` is what selects the tier (Flash vs Pro). Without it, `generate_google()` defaults to `gemini-3.1-flash-image-preview` regardless of what the routing matrix chose.

**Files:**
- Modify: `src/render_funnel.py:100-110,149`
- Test: `tests/test_render_funnel.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_funnel.py`:

```python
class TestCloudModelPassthrough:
    """_generate_cloud should pass model kwarg through to generate_cloud_image."""

    def test_model_passed_to_cloud_generator(self, deck_dir):
        from unittest.mock import patch, MagicMock
        from src.render_funnel import execute_funnel_stage

        mock_result = {
            'file_path': os.path.join(deck_dir, 'images', 'test.png'),
            'provider': 'google',
            'model_used': 'gemini-3.1-flash-image-preview',
            'cost_usd': 0.067,
            'status': 'generated',
        }
        output_path = os.path.join(deck_dir, 'images', 'test.png')

        with patch('src.render_funnel._generate_cloud_raw', return_value=mock_result) as mock_gen:
            execute_funnel_stage(
                deck_dir=deck_dir,
                slide_number=1,
                strategy='full_render',
                prompt='test prompt',
                funnel_stage='cloud_low',
                model='gemini-3.1-flash-image-preview',
                output_path=output_path,
                provider='google',
            )
            mock_gen.assert_called_once()
            call_kwargs = mock_gen.call_args
            # model should be passed through as a kwarg
            assert call_kwargs.kwargs.get('model') == 'gemini-3.1-flash-image-preview' or \
                   ('model' in call_kwargs.kwargs and call_kwargs.kwargs['model'] == 'gemini-3.1-flash-image-preview')

    def test_model_none_omitted_from_cloud_kwargs(self, deck_dir):
        """When model is not provided, don't pass model=None to the generator."""
        from unittest.mock import patch, MagicMock
        from src.render_funnel import execute_funnel_stage

        mock_result = {
            'file_path': os.path.join(deck_dir, 'images', 'test.png'),
            'provider': 'openai',
            'model_used': 'gpt-image-1.5',
            'cost_usd': 0.009,
            'status': 'generated',
        }
        output_path = os.path.join(deck_dir, 'images', 'test.png')

        with patch('src.render_funnel._generate_cloud_raw', return_value=mock_result) as mock_gen:
            execute_funnel_stage(
                deck_dir=deck_dir,
                slide_number=1,
                strategy='full_render',
                prompt='test prompt',
                funnel_stage='cloud_low',
                model='gpt-image-1.5',
                output_path=output_path,
                provider='openai',
            )
            mock_gen.assert_called_once()
            call_kwargs = mock_gen.call_args
            # model SHOULD be passed for all providers now
            assert 'model' in call_kwargs.kwargs
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_render_funnel.py::TestCloudModelPassthrough -v`
Expected: FAIL — `model` not found in call kwargs because `_generate_cloud` doesn't pass it.

- [ ] **Step 3: Write the implementation**

In `src/render_funnel.py`, modify `_generate_cloud()` (lines 100-110) to accept and pass through model:

```python
def _generate_cloud(prompt, provider, output_path, funnel_stage, model=None):
    """Wrapper for cloud generation with funnel-stage-appropriate settings."""
    quality = _CLOUD_STAGE_QUALITY.get(funnel_stage, 'medium')
    size = _CLOUD_STAGE_SIZE.get(funnel_stage, '1536x1024')
    kwargs = {'quality': quality, 'size': size}
    if model:
        kwargs['model'] = model
    return _generate_cloud_raw(
        prompt=prompt,
        provider=provider,
        output_path=output_path,
        **kwargs,
    )
```

Then modify `execute_funnel_stage()` (line 149) to pass model through:

```python
            result = _generate_cloud(prompt, provider, output_path, funnel_stage, model=model)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_render_funnel.py -v`
Expected: ALL pass (existing + new).

- [ ] **Step 5: Commit**

```bash
git add src/render_funnel.py tests/test_render_funnel.py
git commit -m "feat: pass model through render funnel to cloud generator"
```

---

## Task 4: Fix google-image skill provider key and add tier params

The google-image skill hardcodes `provider='google_vertex'` which doesn't match the dispatcher's key (`'google'`). Also add `--model` and `--tier` parameters.

**Files:**
- Modify: `plugins/jack-tar-cloud/skills/google-image/SKILL.md`

- [ ] **Step 1: Update the skill**

In `plugins/jack-tar-cloud/skills/google-image/SKILL.md`:

Replace the argument-hint (line 4):
```yaml
argument-hint: "a description of the image" [--output PATH] [--size SIZE] [--model MODEL] [--tier draft|standard|premium]
```

Replace the Parse Arguments section (lines 34-38):
```markdown
## Parse Arguments

Parse `$ARGUMENTS` for:
- **Prompt**: The quoted description
- **--output PATH**: Where to save (default: `output/google-YYYYMMDD-HHMMSS.png`)
- **--size SIZE**: Dimensions (default: `1536x1024`)
- **--model MODEL**: Specific Google model ID (overrides --tier)
- **--tier TIER**: Shorthand for model selection:
  - `draft` → `imagen-4.0-fast-generate-001` ($0.02)
  - `standard` → `gemini-3.1-flash-image-preview` ($0.067) — default
  - `premium` → `gemini-3-pro-image-preview` ($0.134)

If both `--model` and `--tier` are provided, `--model` takes precedence.
If neither is provided, defaults to `standard` tier (Nanobanana Flash).
```

Replace the Generate section (lines 54-67) — fix `provider='google_vertex'` to `provider='google'` and add model parameter:
```markdown
## Generate

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.generate_cloud_image import generate_cloud_image
result = generate_cloud_image(
    prompt='$PROMPT',
    provider='google',
    output_path='$OUTPUT_PATH',
    model='$MODEL',
)
print(json.dumps(result, indent=2))
"
```

If successful, report the file path, model used, and cost.
If failed, report the error.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-cloud/skills/google-image/SKILL.md
git commit -m "fix: google-image skill uses correct provider key and supports tier selection"
```

---

## Task 5: Update smart router skill for content-aware routing

The smart router currently always prefers FAL, then OpenAI, then Google. Update to consider content suitability.

**Files:**
- Modify: `plugins/jack-tar-cloud/skills/image/SKILL.md`

- [ ] **Step 1: Update routing guidance**

In `plugins/jack-tar-cloud/skills/image/SKILL.md`, replace the "Select Provider and Route" section (lines 56-69):

```markdown
## Select Provider and Route

If `--provider` is specified and available, use it directly.

Otherwise, route based on content suitability:

1. **Text-heavy content** (slides with visible text, labels, diagrams) → prefer Google Nanobanana (best text rendering), then OpenAI, then FAL
2. **Photorealistic imagery** (scenes, people, objects) → prefer FAL FLUX (best photorealism), then OpenAI, then Google
3. **Budget bulk generation** (backgrounds, patterns, simple scenes) → prefer Google Imagen (cheapest at $0.02), then FAL, then OpenAI
4. **Default** (no clear category) → `fal` first, then `openai`, then `google`

When routing to Google, pass the appropriate `--model` based on use case:
- Budget: `--model imagen-4.0-fast-generate-001`
- Standard: `--model gemini-3.1-flash-image-preview`
- Premium: `--model gemini-3-pro-image-preview`

Dispatch the appropriate per-provider skill:
- `fal` → `/jack-tar-cloud:fal-image`
- `openai` → `/jack-tar-cloud:openai-image`
- `google` → `/jack-tar-cloud:google-image`

Pass through all arguments (--output, --size, --model, original prompt).

If the first provider fails, try the next available provider in the priority order.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-cloud/skills/image/SKILL.md
git commit -m "feat: smart router considers content suitability for provider selection"
```

---

## Task 6: Update verify skill to report Google tiers

Report Nanobanana and Imagen readiness separately instead of a single binary Google status.

**Files:**
- Modify: `plugins/jack-tar-cloud/skills/verify/SKILL.md`

- [ ] **Step 1: Update the provider check and status reporting**

In `plugins/jack-tar-cloud/skills/verify/SKILL.md`, replace the Step 2 provider check (lines 42-55) with:

```markdown
## Step 2: Check provider API keys

```bash
python3 -c "
import os
providers = {
    'openai': bool(os.environ.get('OPENAI_API_KEY')),
    'google': bool(os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GOOGLE_API_KEY')),
    'fal': bool(os.environ.get('FAL_KEY')),
}
# Recraft uses OPENAI_API_KEY
providers['recraft'] = providers['openai']
import json
print(json.dumps(providers))
"
```
```

Replace the example output (lines 65-90) with:

```markdown
Example output:

```
PLUGIN: jack-tar-cloud
VERSION: 1.0.0

DEPENDENCIES:
  Python:          READY (3.12.x)
  requests:        READY
  openai:          READY
  google-genai:    READY
  fal-client:      READY

PROVIDERS:
  openai:              READY (OPENAI_API_KEY set)
  google-nanobanana:    READY (Flash + Pro via GOOGLE_API_KEY)
  google-imagen:        READY (Fast + Standard via GOOGLE_API_KEY)
  fal:                  READY (FAL_KEY set)
  recraft:              READY (uses OPENAI_API_KEY)

GOOGLE TIERS:
  Nanobanana Flash:    gemini-3.1-flash-image-preview     $0.067/image  (best text rendering)
  Nanobanana Pro:      gemini-3-pro-image-preview          $0.134/image  (premium quality)
  Imagen Fast:         imagen-4.0-fast-generate-001        $0.020/image  (budget bulk)
  Imagen Standard:     imagen-4.0-generate-001             $0.040/image  (standard quality)

CAPABILITIES:
  image:           READY (3/4 providers available)
  icon:            READY (recraft available)

STATUS: PARTIALLY_AVAILABLE
REASON: All providers configured
```
```

When Google is available, report both sub-families. When not available, show a single `google: NOT_READY` line.

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-cloud/skills/verify/SKILL.md
git commit -m "feat: verify skill reports Google tiers separately"
```

---

## Task 7: Document tier selection in imagegen-bridge

Update the imagegen-bridge skill's Step 9A and cloud generation docs to reference tier selection from the routing matrix.

**Files:**
- Modify: `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md`

- [ ] **Step 1: Update cloud image generation command docs**

In `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md`, update the cloud generation command (around line 317-320):

```markdown
### For jack-tar-cloud:image (hero/pattern in production mode):
```bash
/jack-tar-cloud:image "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-TYPE.png --provider PROVIDER --model MODEL
```

When provider is `google`, the `--model` parameter selects the tier:
- Draft/budget: `--model imagen-4.0-fast-generate-001` ($0.02)
- Standard production: `--model gemini-3.1-flash-image-preview` ($0.067)
- Premium (text-heavy, complex): `--model gemini-3-pro-image-preview` ($0.134)

The routing matrix and production-upgrade-plan already specify the correct model. Use the model from the plan entry directly — do NOT hardcode model names in the bridge.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md
git commit -m "docs: document Google tier selection in imagegen-bridge"
```
