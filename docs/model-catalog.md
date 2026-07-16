# Model Catalog

<!-- AUTO-GENERATED from model-catalog/model-catalog.json — do not edit by hand. -->
<!-- Regenerate with: python model-catalog/catalog_markdown.py -->

Catalog version **1.1.0**, updated **2026-07-15**, min loader version 1.

Single source of truth for model identity, capability, and pricing across all jack-tar plugins (EPIC #125). Loaded by `model_catalog.py` with shipped → cached-remote → local-config precedence.

## Role defaults

| Role | Default |
|---|---|
| icon | `recraft-v4-svg` |
| image_gen | `gemini-3.1-flash-image` |
| local_draft | `x/flux2-klein → x/z-image-turbo` |
| vlm_json | `gemini-3.5-flash` |

## FAL.ai

| Model | Status | Roles | Resolutions | Pricing (USD) | Quirks | Aliases |
|---|---|---|---|---|---|---|
| `fal-ai/flux-2-pro` | active | image_gen | 1K, 2K | $0.030 first MP + $0.015/extra MP | — | `flux-2-pro` |
| `fal-ai/flux-2-klein` | active | image_gen | 1K | $0.014 flat | — | `flux-2-klein` |
| `fal-ai/ideogram/v3` | active | image_gen | 1K | $0.060 flat *(estimate)* | — | `ideogram-3` |

## Google (Nano Banana + Imagen)

| Model | Status | Roles | Resolutions | Pricing (USD) | Quirks | Aliases |
|---|---|---|---|---|---|---|
| `gemini-3.1-flash-image` | active | image_gen | 512, 1K, 2K, 4K | 512 $0.045; 1K $0.067; 2K $0.101; 4K $0.151 | no_negative_prompt | `gemini-3.1-flash-image-preview` |
| `gemini-3-pro-image` | active | image_gen | 1K, 2K, 4K | 1K $0.134; 2K $0.134; 4K $0.240 | no_negative_prompt | `gemini-3-pro-image-preview` |
| `imagen-4.0-fast-generate-001` | active | image_gen | 1K | vertex: 1K $0.020; developer: 1K $0.020 | fixed_resolution, no_negative_prompt | `imagen-4-fast` |
| `imagen-4.0-generate-001` | active | image_gen | 1K, 2K | vertex: 1K $0.040, 2K $0.040; developer: 1K $0.040, 2K $0.101 | no_negative_prompt | `imagen-4`, `imagen-4-standard` |
| `imagen-4.0-ultra-generate-001` | active | image_gen | 1K, 2K | vertex: 1K $0.060, 2K $0.060; developer: 1K $0.060, 2K $0.101 | no_negative_prompt | `imagen-4-ultra` |
| `gemini-3.5-flash` | active | vlm, vlm_json | — | — | — | — |
| `gemini-2.5-flash` | deprecated → `gemini-3.5-flash` | vlm | — | — | thinking | — |
| `gemini-2.0-flash` | retired → `gemini-3.5-flash` | vlm, vlm_json | — | — | — | — |

## MLX (local, free)

| Model | Status | Roles | Resolutions | Pricing (USD) | Quirks | Aliases |
|---|---|---|---|---|---|---|
| `mlx/flux2-klein-4b` | active | image_gen, local_draft | 1K | $0.000 flat | mflux_metadata_sidecar_null | `flux2-klein-4b-mflux` |
| `mlx/z-image-turbo` | active | image_gen, local_draft | 1K | $0.000 flat | — | `z-image-turbo-mflux` |
| `mlx/qwen-image` | active | image_gen, local_draft | 1K | $0.000 flat | — | `qwen-image-mflux` |

## Ollama (local, free)

| Model | Status | Roles | Resolutions | Pricing (USD) | Quirks | Aliases |
|---|---|---|---|---|---|---|
| `x/flux2-klein` | active | image_gen, local_draft | 1K | $0.000 flat | — | — |
| `x/z-image-turbo` | active | image_gen, local_draft | 1K | $0.000 flat | — | — |

## OpenAI

| Model | Status | Roles | Resolutions | Pricing (USD) | Quirks | Aliases |
|---|---|---|---|---|---|---|
| `gpt-image-1.5` | active | image_gen | 1K | $0.009–$0.200 by size×quality | no_negative_prompt | — |

## Recraft

| Model | Status | Roles | Resolutions | Pricing (USD) | Quirks | Aliases |
|---|---|---|---|---|---|---|
| `recraft-v4-standard` | active | image_gen | 1K | 1K $0.040 | — | `recraft-v4` |
| `recraft-v4-pro` | active | image_gen | 2K, 4K | 2K $0.250; 4K $0.500 *(estimate)* | upscale_chain_4k | — |
| `recraft-v4-svg` | active | icon | — | standard $0.08; pro $0.30 | — | `recraftv4` |

## Notes

- **`gemini-3.1-flash-image`** — Nano Banana Flash. The '-preview' suffixed id was deprecated upstream (issue #123, verified 2026-07-15); alias retained so existing manifests and callers resolve.
- **`gemini-3.1-flash-image` pricing** — EPIC #58 pricing table; reconciled issue #113 AC6. Token rates from ai.google.dev/gemini-api/docs/pricing (captured 2026-05-21).
- **`gemini-3-pro-image`** — Nano Banana Pro — best in-image text rendering. '-preview' id deprecated upstream (issue #123).
- **`gemini-3-pro-image` pricing** — Pro 2K priced identically to Pro 1K (issue #113 AC6 reconciliation). Token rates from ai.google.dev/gemini-api/docs/pricing (captured 2026-05-21).
- **`imagen-4.0-fast-generate-001`** — Fixed native resolution — rejects image_size/sampleImageSize with 400 INVALID_ARGUMENT (issue #74). 'imagen-4-fast' is the router-side alias.
- **`imagen-4.0-generate-001` pricing** — Dual pricing: Vertex (GOOGLE_APPLICATION_CREDENTIALS) flat per-image; Gemini Developer API (GOOGLE_API_KEY only) token-based, 2K dearer.
- **`imagen-4.0-ultra-generate-001` pricing** — Developer-API 2K treated as token-based like Standard.
- **`gpt-image-1.5` pricing** — token_rates are UNVERIFIED_ESTIMATE — all OpenAI pricing URLs 403/404'd during the 2026-05-21 spike; community-cited placeholders pending dashboard verification (see docs/spikes/2026-05-21-actual-token-pricing/).
- **`fal-ai/flux-2-pro`** — Caps at 2048x2048.
- **`fal-ai/flux-2-pro` pricing** — ~$0.045 for 1920x1080. budget_tracker previously carried a divergent $0.050 flat figure — the tiered rate here is canonical (EPIC #125).
- **`fal-ai/ideogram/v3` pricing** — Published range $0.030-$0.090; midpoint used.
- **`recraft-v4-standard`** — Router-side id; dispatch picks the actual endpoint by tier+resolution (issue #61).
- **`recraft-v4-standard` pricing** — Verified via fal.ai/models/fal-ai/recraft/v4/*.
- **`recraft-v4-pro` pricing** — 4K = 2K generation ($0.25) + Creative Upscale ($0.25 FAL-parity assumption — direct-API upscale price not published; env override honoured when positive).
- **`recraft-v4-svg` pricing** — Same rates via direct API and the FAL route (fal-ai/recraft/v4/text-to-vector). budget_tracker previously carried divergent $0.04/$0.08 svg/png figures — per_tier here is canonical (EPIC #125).
- **`x/flux2-klein`** — Tag-prefix entry: exact installed tag (e.g. x/flux2-klein:9b) resolves at runtime via /api/tags — never hardcode tags. Preferred local model for academic figures (F16 audit: Klein 9b at 8/9 on the deck-schema brief).
- **`x/z-image-turbo`** — Fast local draft fallback when flux2-klein is not pulled.
- **`gemini-3.5-flash`** — Verified 2026-07-15 (issue #123): non-thinking for retriever/planning steps, clean JSON output for paperbanana's parser, publication-quality academic figures in 2-3 iterations at ~$0.02/diagram.
- **`gemini-2.5-flash`** — Thinking model — reasoning tokens break strict-JSON parsers (paperbanana retriever loops to ~17min timeout, issues #122/#123). NOT eligible for the vlm_json role. Deprecated as a jack-tar default in favour of gemini-3.5-flash.
- **`gemini-2.0-flash`** — Retired upstream — 404 NOT_FOUND 'This model is no longer available' (verified 2026-07-15, issue #123).
- **`mlx/flux2-klein-4b`** — FLUX.2 Klein 4B via mflux. Primary: pre-quantized 4-bit community export (4.3 GB, fast cold-load, requires mflux >= 0.16; licence CONFIRMED apache-2.0 via HF model card metadata, issue #124 OQ-A — same terms as the base model, no relicensing). Fallback: black-forest-labs/FLUX.2-klein-4B (Apache 2.0, ~13 GB, quantized 4-bit on load). default_steps 4 is the family-native distilled value; render_steps 20 is what the pipeline passes — the 2026-07-11 dogfood showed 4B reaches Klein-9b grade at 20 steps + annotation pattern. MLX default draft model. Horizon-2 gate: Phase 5 dogfood must beat/match the Ollama Klein-9b 8/9 baseline before promotion into role_defaults.local_draft. Field finding 2026-07-15: mflux 0.18.0 writes a literal-null .metadata.json sidecar for this family; generation metadata IS embedded in the PNG XMP/IPTC — consumers must not rely on the sidecar.
- **`mlx/z-image-turbo`** — Z-Image-Turbo via mflux, requires mflux >= 0.13. SMOKE RESULT 2026-07-16 (M2 Max 32 GB, 9 steps, seed 42): 9/10 on BOTH the exact-spellings and natural-prose dialects — labels letter-perfect, flat clean white background (flat-field noise sigma 0.43, statistically identical to Klein's 0.42), no grain, ~62 s/render at 1024x576. The Ollama-variant retirement for schema figures (2026-07-11 dogfood: paradigm drift on prose, 1-2/9) does NOT reproduce in this mflux 4-bit port — that verdict was variant-specific. First-class draft model alongside Klein 4B. LICENCE NOTE (issue #124 review M6, CONFIRMED via HF model card metadata): the pre-quantized primary repo filipstrand/Z-Image-Turbo-mflux-4bit is licensed 'tongyi-qianwen-license' (license:other tag), NOT Apache 2.0 — the derivative repo's licence governs the download. Operators needing pure Apache 2.0 should pull the fallback Tongyi-MAI/Z-Image-Turbo (Apache 2.0, confirmed via HF model card, full precision, quantized 4-bit on load) instead. 9-step distilled (render_steps == default_steps). timeout_seconds 180 is a conservative placeholder — Mac wall-clock unpublished; Phase 5 measures (proposal risk 2).
- **`mlx/qwen-image`** — Qwen-Image via mflux, requires mflux >= 0.11. REPO SWAP 2026-07-15 (issue #296 upstream): the previous primary filipstrand/Qwen-Image-mflux-6bit was saved with mflux 0.11.0 (safetensors header metadata) and is BROKEN on mflux >= 0.13 — the v0.13 weight-loading refactor broke all pre-0.13 pre-quantized exports (https://github.com/filipstrand/mflux/issues/296, open; maintainer acknowledged 2025-12-17, HF weights never re-uploaded). Failure mode: quantized text-encoder embedding not reconstructed — packed U32 rows (broadcast_shapes (3584) vs (1,N,672)). Do NOT reuse that repo. New primary OsaurusAI/Qwen-Image-mflux-4bit: 25.9 GB, license apache-2.0 (verified via HF API cardData 2026-07-15), ungated, quantized WITH mflux 0.18 (the version this pipeline targets) — mflux-format exports record mflux_version in their safetensors headers, so version-matched saves are the fix. SMOKE RESULT 2026-07-15 (M2 Max 32 GB): loads + renders OK on mflux 0.18.0 — confirms the vintage diagnosis (52 s load-test; 5m35s at 1024x576/20 steps, no OOM without --low-ram). BUT text fidelity at 4-bit scored 4/10 vs Klein 4B's 9/10 on the identical exact-spellings prompt/seed (misspelled label 'Publiish', hallucinated garbled banner, noisy non-white background) — consistent with the upstream quantization-degradation caution below. DEFINITIVE ISOLATION SERIES 2026-07-16 (5 renders, seed 42): (1) PROMPT DIALECT is decisive — Klein-style patterns (letter-by-letter spell-outs, 'box one' meta-language) produce garbled labels + hallucinated captions; natural prose with double-quoted labels ('a box labeled "Publish"') produced letter-perfect text in 3/3 renders (community-measured ~96% quoted vs ~65% unquoted). (2) Negative prompts are PLACEBO — Qwen-Image is not trained on negative conditioning; pass ' '. (3) The grain is PER-STEP COMPOUNDING QUANTIZATION ERROR, not a fixed floor: flat-field sweep (512px, seed 42) shows high-freq noise growing monotonically with steps (sigma 2.48 @ 4 steps -> 4.14 @ 8 -> 6.42 @ 20 -> 7.36 @ 50) while whites drift dingy (252 -> 224) — every step passes through the q4 transformer, so more steps = more accumulated error. The canonical more-steps-better recipe is INVERTED on this export (same pathology class as the Klein F8 step-curve finding). (4) Practical curve is U-shaped: 4 steps under-forms structure (ghost outlines, chroma fringing on glyphs, 3/10); 8 STEPS IS THE SWEET SPOT — 7/10 (perfect text, solid structure, lighter-but-visible grain) at ~2.5 min, matching the 30-step score at 3.4x less time. render_steps set to 8 on this evidence. (5) The 7/10 grain ceiling stands at every tested config — vs Klein 4B 9/10 in 35 s. VERDICT: usable-with-caveats for schema work at 8 steps if Klein is unavailable; never preferred over Klein. Better ceiling needs the 8-bit export (36 GB, >=48 GB machines) or the post-#420 mixed-precision 4-bit. text_rendering downgraded excellent -> good: 'excellent' described full precision, not this tier. Fallback stays Qwen/Qwen-Image (apache-2.0) but its true size is ~58 GB (upstream qwen README), not the ~40 GB previously documented; mflux-save local re-quantization is NOT viable under ~57 GB free RAM (no layer-streaming, confirmed from mflux source). Upstream quality note (mflux qwen README): '6-bit or below can degrade the image a lot more compared to Flux' — quantization quality must be evaluated in Phase 5; 0.18-era saves are mixed-precision (hence 4-bit = 25.9 GB). min_ram_gb 32 sized for the 4-bit primary (25.9 GB weights + activations; operators should pass --low-ram if headroom is tight). Strongest open-weights in-image text renderer AT FULL PRECISION; the 4-bit tier this entry ships did not show that advantage in the 2026-07-15 smoke. Upstream README examples use --steps 30; render_steps stays 20 (mflux family default) pending Phase 5 measurement. timeout_seconds 900 remains a placeholder pending Phase 5 (§10 OQ-B).
