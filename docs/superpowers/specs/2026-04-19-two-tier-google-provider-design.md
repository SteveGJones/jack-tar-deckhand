# Two-Tier Google Provider Support

## Problem

The design spec (`2026-03-31-production-rendering-engine-strategy.md`) and the image-generation-expert agent already document two distinct Google image generation tiers: Nanobanana (premium, Gemini models) and Imagen (cheap, like FLUX). The implementation code hasn't caught up — `provider_discovery.py` hardcodes `'imagen-4'`, `image_router.py` uses abstract model names that don't map to real API IDs, `render_funnel.py` assumes all cloud providers use OpenAI's quality parameter, and four skill files have stale references.

Dogfood finding (2026-04-19): used `imagen-4.0-ultra-generate-001` thinking it was Nanobanana. The garbled text in the output (which Nanobanana handles well) revealed the wrong model family was being called. The two families use completely different APIs:

- **Nanobanana** = Gemini image models, `generate_content` API with `response_modalities=["IMAGE", "TEXT"]`
  - Flash: `gemini-3.1-flash-image-preview` ($0.067/image)
  - Pro: `gemini-3-pro-image-preview` ($0.134/image)

- **Imagen** = `imagen-4.0-*` models, `generate_images` API
  - Fast: `imagen-4.0-fast-generate-001` ($0.020/image)
  - Standard: `imagen-4.0-generate-001` ($0.040/image)

## Solution

Implementation catch-up across four code files and four skill files. No new design — implement what the existing spec already says.

## 1. provider_discovery.py

**Current:** Line 37 hardcodes `'imagen-4'` as default Google model. Returns single `available` boolean.

**Change:** When `GOOGLE_API_KEY` is set, report all available tiers:

```python
"google": {
    "available": True,
    "tiers": {
        "nanobanana_flash": {"model": "gemini-3.1-flash-image-preview", "cost": 0.067},
        "nanobanana_pro": {"model": "gemini-3-pro-image-preview", "cost": 0.134},
        "imagen_fast": {"model": "imagen-4.0-fast-generate-001", "cost": 0.020},
        "imagen_standard": {"model": "imagen-4.0-generate-001", "cost": 0.040},
    }
}
```

Both API families use the same `GOOGLE_API_KEY`. If the key is set, all four models are available. No per-tier detection needed.

## 2. image_router.py

**Current:** Routing matrix uses abstract names (`'imagen-4-standard'`, `'imagen-4-fast'`) that don't exist in the API. No tier field on `RoutingTarget`.

**Changes:**

Add `tier` field to `RoutingTarget` namedtuple: `(skill, provider, model, cost_per_image, tier)` where tier is `'draft'`, `'standard'`, or `'premium'`.

Replace Google entries in routing matrix with real model IDs:

| Use case | Current | New model | Cost | Tier |
|----------|---------|-----------|------|------|
| Draft/budget hero | `imagen-4-fast` | `imagen-4.0-fast-generate-001` | $0.02 | draft |
| Production hero | `imagen-4-standard` | `gemini-3.1-flash-image-preview` | $0.067 | standard |
| Premium (text, complex) | not in matrix | `gemini-3-pro-image-preview` | $0.134 | premium |
| Pattern/background budget | `imagen-4-fast` | `imagen-4.0-fast-generate-001` | $0.02 | draft |

Imagen is the cheap option alongside FLUX. Nanobanana Flash is standard production. Nanobanana Pro is premium — used when the prompt refinement loop (Spec 1) escalates to it.

`plan_production_upgrade()` gains a `recommended_tier` field in its output entries, read by the imagegen-bridge to decide Flash vs Pro.

## 3. render_funnel.py

**Current:** Uses `quality` parameter (`'low'`/`'medium'`) which is an OpenAI concept. Google Nanobanana doesn't have quality — tier selection is a different model entirely.

**Change:** When building parameters for a cloud stage, check the provider and pass the right parameter:

- **OpenAI:** `quality='low'` / `quality='medium'` (unchanged)
- **FAL/FLUX:** `size` parameter (unchanged)
- **Google Nanobanana:** `model` parameter selects the tier — Flash for `cloud_low`, Pro for `cloud_full`
- **Google Imagen:** `model` parameter selects the tier — Fast for `cloud_low`, Standard for `cloud_full`

No new abstraction. The funnel's `_generate_cloud()` wrapper already passes `model` through to `generate_cloud_image()`. The change is making the funnel stage → model mapping provider-aware instead of assuming all clouds use OpenAI's quality parameter.

## 4. Skill file fixes

### google-image/SKILL.md

Replace `provider='google_vertex'` with `provider='google'`. Add `--model` parameter documentation listing the four available models. Add `--tier` shorthand:
- `--tier draft` → `imagen-4.0-fast-generate-001`
- `--tier standard` → `gemini-3.1-flash-image-preview`
- `--tier premium` → `gemini-3-pro-image-preview`

### image/SKILL.md (smart router)

Update routing priority. Currently says "google last". Should route based on content suitability:
- Nanobanana Flash preferred for text-heavy content (best text rendering)
- FLUX for photorealism
- Imagen for budget bulk generation

### verify/SKILL.md

Report Google tiers separately instead of single boolean:

```
  google-nanobanana: READY (Flash + Pro, GOOGLE_API_KEY set)
  google-imagen:     READY (Fast + Standard, GOOGLE_API_KEY set)
```

### imagegen-bridge/SKILL.md

Step 9A documents `--provider PROVIDER --model MODEL` but doesn't document tier selection. Add guidance: bridge reads `recommended_tier` from the production-upgrade-plan and maps it to the correct model ID via the routing matrix.

## Not In Scope

- Changes to `generate_cloud_image.py` — it already handles both APIs correctly (lines 266-336, model set routing at lines 78-86)
- Changes to image-generation-expert agent — already documents both tiers correctly
- Changes to production-rendering-engine-strategy spec — already comprehensive
- The prompt refinement loop — that's Spec 1 (cross-tier prompt refinement)
