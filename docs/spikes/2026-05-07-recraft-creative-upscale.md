# Spike — Recraft V4 raster + Creative Upscale endpoints (Issue #61)

**Date:** 2026-05-07
**Outcome:** ✅ Endpoints + pricing confirmed for FAL route; direct-API upscale price unverified (assume parity, verify in first test)
**Decision:** proceed with single-PR implementation per Issue #61 plan; 4K path = generate at 2K → Creative Upscale chain

## Question

Issue #61 spec said: *"Verify the FAL endpoint name and cost during implementation. May be a separate `fal-ai/recraft/upscale` call chained after the initial generation."* Need to confirm endpoint name, pricing, and the dual-path (FAL vs direct Recraft API) parity before drafting the implementation plan.

## Findings

### FAL.ai endpoints (verified)

| Tier | Endpoint | Cost | Output |
|---|---|---|---|
| 1K | `fal-ai/recraft/v4/text-to-image` | $0.04 | 1024² |
| 2K | `fal-ai/recraft/v4/pro/text-to-image` | $0.25 | 2048² |
| Upscale | `fal-ai/recraft/upscale/creative` | $0.25 | up to 4096² (input-dependent factor) |
| 4K (chained) | 2K Pro → Creative Upscale | **$0.50** total | up to 4096² |

The FAL Creative Upscale page does not state a fixed output resolution — it says the service "increases image resolution and makes the image sharper and cleaner." Practical cap is ~4096px per the direct-API constraints (see below).

### Recraft direct API endpoints (verified)

- Base URL: `https://external.api.recraft.ai/v1`
- Generate raster: `POST /images/generations` with `model: 'recraftv4'`, `style: 'realistic_image' | 'digital_illustration' | ...` (existing icon code uses this OpenAI-compatible shape with `extra_body` controls)
- Upscale: `POST /images/creativeUpscale` (multipart/form-data, file=image)
- Constraints: input image ≤5MB, ≤16MP, max dim ≤4096px, min dim ≥256px

**Upscale pricing on direct API**: not surfaced in public docs as of this spike. We will:
1. Cost-table at $0.25 (FAL parity) as best estimate
2. Log a clear `TODO(verify-upscale-cost)` in the cost-helper docstring
3. Surface the actual figure when first production call lands (real cost is in the API response or the user's billing dashboard)

### Brand-color parameter format

Direct API: `controls.colors = [{rgb: [r, g, b]}, ...]` (existing pattern from `generate_recraft_direct` in `generate_cloud_icon.py`)
FAL: `arguments.colors = [{r: r, g: g, b: b}, ...]` (existing pattern from `generate_fal_recraft`)

Both formats already implemented for the SVG icon path. Lift the same translation logic for raster.

## Cost trade-off vs Nano Banana Pro

| Need | Best provider | 4K cost |
|---|---|---|
| Photorealistic detail | Nano Banana Pro | $0.24 |
| Brand-color fidelity (≥3 specified hexes) | Recraft V4 raster + upscale | $0.50 |
| Design taste, schematic, infographic style | Recraft V4 raster + upscale | $0.50 |

Recraft 4K is **~2× the cost** of Nano Banana Pro 4K. The router's 4K decision rule must make this explicit:
- Default 4K → Nano Banana Pro (cost-efficient)
- `slide.brand_fidelity == "exact"` AND palette has ≥3 specified hexes → Recraft 4K (brand-fidelity premium)

## Decisions baked into the plan

1. **Implement 4K via generate-2K → Creative Upscale chain.** No fall-back; if upscale fails, surface the error rather than returning the 2K image silently.
2. **Direct-API price for upscale = $0.25 (assumed parity)** with TODO comment. Cost helper accepts an override env var (`RECRAFT_UPSCALE_COST_USD`) so a corrected price can be hot-fixed without a code change if the assumption is wrong.
3. **Brand-fidelity flag is explicit per-slide** (`slide.brand_fidelity: "exact" | "approximate" | "none"`), not inferred from palette size. Speaker control over the 2× cost premium.
4. **No upscale support without prior generation.** The new `generate_recraft` accepts `resolution='4K'` only via internal chain; we do NOT expose `creativeUpscale` as a standalone provider call in this PR (keeps the API surface small).

## References

- [Recraft Creative Upscale | fal.ai](https://fal.ai/models/fal-ai/recraft/upscale/creative)
- [Recraft V4 Pro Text-to-Image | fal.ai](https://fal.ai/models/fal-ai/recraft/v4/pro/text-to-image)
- [Recraft API Documentation](https://webflow.recraft.ai/docs)
- Existing dual-path pattern: `plugins/jack-tar-cloud/src/generate_cloud_icon.py:65-189`
