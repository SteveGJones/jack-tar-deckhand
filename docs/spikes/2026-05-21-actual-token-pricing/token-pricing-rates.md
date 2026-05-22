# Token Pricing Rates — Image Generation Providers

**Spike:** Actual-token pricing vs catalog estimates for image generation APIs
**Task:** 4 of 22
**Date captured:** 2026-05-21
**Coverage:** Gemini Developer API (Nano Banana models), Imagen 4 (Gemini Developer API), OpenAI gpt-image-1

---

## Google Gemini Nano Banana — Flash

- **Model:** `gemini-3.1-flash-image-preview`
- **API track:** Gemini Developer API (API key — NOT Vertex AI)
- **Text / image input rate:** $0.50 per 1M tokens
- **Image output rate:** $60.00 per 1M tokens
- **Per-image output costs by resolution (derived from token counts):**
  - 0.5K (512 × 512 px): 747 tokens → **$0.045 per image**
  - 1K (1024 × 1024 px): 1,120 tokens → **$0.067 per image**
  - 2K (2048 × 2048 px): 1,680 tokens → **$0.101 per image**
  - 4K (4096 × 4096 px): 2,520 tokens → **$0.151 per image**
- **Batch tier (50% discount):**
  - Text / image input: $0.25 per 1M tokens
  - Image output: $30.00 per 1M tokens
  - **Per-image output costs by resolution (batch tier, derived from token counts):**
    - 0.5K: 747 tokens × $30.00 / 1,000,000 = **$0.022 per image**
    - 1K: 1,120 tokens × $30.00 / 1,000,000 = **$0.034 per image**
    - 2K: 1,680 tokens × $30.00 / 1,000,000 = **$0.050 per image**
    - 4K: 2,520 tokens × $30.00 / 1,000,000 = **$0.076 per image**
- **Free tier:** Not available for this model
- **Source:** https://ai.google.dev/gemini-api/docs/pricing
- **Date captured:** 2026-05-21
- **Notes:**
  - Input images are counted at 560 tokens per image (standardised flat rate for input).
  - Output token counts above are the SDK-observed values per resolution tier; multiply by $60.00 / 1,000,000 to get per-image cost.
  - `usage_metadata.candidates_tokens_details` with `modality=IMAGE` is the runtime field that carries these output token counts (see `phase-0-discovery.md`).
  - These are the rates used in `src/actual_cost_calculator.py` for Nano Banana Flash actual-cost tracking (Tasks 5, 12).

---

## Google Gemini Nano Banana — Pro

- **Model:** `gemini-3-pro-image-preview`
- **API track:** Gemini Developer API (API key — NOT Vertex AI)
- **Text / image input rate:** $2.00 per 1M tokens
- **Image output rate:** $120.00 per 1M tokens
- **Per-image output costs by resolution (derived from token counts):**
  - 1K / 2K (1024–2048 px): 1,120 tokens → **$0.134 per image**
  - 4K (4096 × 4096 px): 2,000 tokens → **$0.240 per image**
- **Batch tier (50% discount):**
  - Text / image input: $1.00 per 1M tokens
  - Image output: $60.00 per 1M tokens (50% of $120.00)
  - **Per-image output costs by resolution (batch tier, derived from token counts):**
    - 1K / 2K: 1,120 tokens × $60.00 / 1,000,000 = **$0.067 per image**
    - 4K: 2,000 tokens × $60.00 / 1,000,000 = **$0.120 per image**
- **Free tier:** Not available for this model
- **Source:** https://ai.google.dev/gemini-api/docs/pricing
- **Date captured:** 2026-05-21
- **Notes:**
  - Input images counted at 560 tokens per image (same standardised rate as Flash).
  - No separate 0.5K tier documented for Pro; the 1K/2K tier uses 1,120 tokens regardless of whether 1K or 2K is requested.
  - These are the rates used in `src/actual_cost_calculator.py` for Nano Banana Pro actual-cost tracking (Tasks 12, 19).

---

## Google Imagen 4 (Gemini Developer API)

- **Models:**
  - `imagen-4.0-fast-generate-001` — Fast tier
  - `imagen-4.0-generate-001` — Standard tier
  - `imagen-4.0-ultra-generate-001` — Ultra tier
- **API track:** Gemini Developer API (API key — NOT Vertex AI)
- **Pricing model:** Flat per-image (NOT token-based)
- **Rates:**
  - Fast: **$0.020 per image**
  - Standard: **$0.040 per image**
  - Ultra: **$0.060 per image**
- **Text input rate:** N/A — no token-based input billing published; flat per-image rate covers the full call
- **Image output rate:** N/A — not expressed per-token; flat per-image only
- **Free tier:** Not available for any Imagen 4 model
- **Source:** https://ai.google.dev/gemini-api/docs/pricing
- **Date captured:** 2026-05-21
- **Notes:**
  - `GenerateImagesResponse` has no `usage` or `usage_metadata` field (confirmed by SDK inspection in `phase-0-discovery.md`). Token-based actual-cost tracking is NOT possible for Imagen.
  - Catalog-only billing applies: jack-tar cost estimates for Imagen use these flat rates directly. Task 6 (Imagen actual-cost path) is SKIPPED — there is no runtime usage field to read.
  - No resolution-based pricing tiers published; the flat rate applies regardless of the `image_size` parameter.
  - Vertex AI Imagen pricing is separate (SKU-based) and was not confirmed reachable at `cloud.google.com/vertex-ai/generative-ai/pricing#imagen-models` — the page redirected to a Gemini Agent Platform pricing view that did not include Imagen SKUs. Vertex AI rates are out of scope for this spike (jack-tar uses the Gemini Developer API track).

---

## Existing code discrepancies (spike findings)

### Imagen Developer API 2K — codebase appears to over-estimate

`plugins/jack-tar-cloud/src/generate_cloud_image.py:298-306` defines `_IMAGEN_DEVELOPER_COSTS` with 2K rates ($0.101 for Standard and Ultra) that **do not match** the published flat-per-image rates ($0.040 Standard, $0.060 Ultra) captured above.

The code comment ("1K matches Vertex flat; 2K is dearer (1680 tokens at the Imagen rate)") asserts a token-based billing model for Imagen on the Gemini Developer API. However, Phase 0 SDK inspection (`phase-0-discovery.md`) confirmed `GenerateImagesResponse` exposes **no usage_metadata field at all**, and the official pricing page lists Imagen as flat per-image regardless of resolution.

**Hypothesis:** the codebase comment is stale or was based on a conservative worst-case estimate that did not survive into the live pricing page. The $0.101 rate over-estimates the published $0.040 / $0.060 flat rates by 2.5× / 1.7× respectively.

**Verification path:** this hypothesis can only be confirmed by examining the Google billing console after a real Imagen 2K call (out of scope for Phase 1, which has no usage_metadata to compare). For now, this finding is documented but the codebase remains unchanged pending billing-console verification.

**Impact on Phase 2 refactor (if pursued):** if the codebase is over-estimating Imagen 2K, the `_IMAGEN_DEVELOPER_COSTS` table should be flattened to match the published rates. This is the kind of correction the spike's hypothesis predicts. Track as a follow-up after Phase 1 GO verdict.

---

## OpenAI gpt-image-1

- **Model:** `gpt-image-1`
- **Text input rate:** rate not published on this page — defer to live billing observation
- **Image output rate:** rate not published on this page — defer to live billing observation
- **Source attempted:** https://openai.com/api/pricing/ (HTTP 403 Forbidden — Cloudflare blocked all fetch attempts)
- **Date captured:** 2026-05-21
- **Notes:**
  - All OpenAI pricing URLs returned HTTP 403 during this spike: `openai.com/api/pricing/`, `platform.openai.com/docs/pricing`, `platform.openai.com/docs/guides/image-generation`, `help.openai.com/en/articles/10362006-gpt-image-1-api-pricing`, `openai.com/research/gpt-image-1`. No cached or archived version was accessible via WebFetch.
  - The `phase-0-discovery.md` doc (Task 2) contained an incidental mention of "$0.04/1M input, $0.04/1M output as of 2026-05-21 public pricing" — but this was an inference in that doc, not extracted from a verifiable source page. It is NOT reproduced here to avoid laundering an unverified number into a rate table.
  - The SDK field structure IS confirmed: `response.usage` with `input_tokens`, `output_tokens`, `total_tokens`, `input_tokens_details.text_tokens`, `input_tokens_details.image_tokens`, `output_tokens_details.image_tokens` (see `phase-0-discovery.md`).
  - **Action for Task 7:** Before implementing the OpenAI actual-cost path, retrieve current rates from the OpenAI dashboard's [Usage & Pricing page](https://platform.openai.com/settings/organization/billing/overview) or from the live API response's `usage` object under a real test call, then update this doc with `date_captured` before committing Task 7.
  - If the phase-0 inference ($0.04/1M input, $0.04/1M output) is used as a working estimate in Task 7, it must be flagged as `UNVERIFIED_ESTIMATE` in the calculator and in comments until a live source confirms it.

---

## Summary Table

| Provider | Model | Input $/MTok | Output $/MTok | Output $/image (1K) | Source reachable? |
|----------|-------|--------------|---------------|----------------------|-------------------|
| Google Nano Banana | `gemini-3.1-flash-image-preview` | $0.50 | $60.00 | $0.067 | YES |
| Google Nano Banana | `gemini-3-pro-image-preview` | $2.00 | $120.00 | $0.134 | YES |
| Google Imagen 4 | `imagen-4.0-fast-generate-001` | N/A (flat) | N/A (flat) | $0.020 (flat) | YES |
| Google Imagen 4 | `imagen-4.0-generate-001` | N/A (flat) | N/A (flat) | $0.040 (flat) | YES |
| Google Imagen 4 | `imagen-4.0-ultra-generate-001` | N/A (flat) | N/A (flat) | $0.060 (flat) | YES |
| OpenAI | `gpt-image-1` | NOT CAPTURED | NOT CAPTURED | NOT CAPTURED | NO (403) |

---

## Re-validation Guidance

Pricing pages change without notice. Before any production spend:

1. **Gemini Developer API** — verify at https://ai.google.dev/gemini-api/docs/pricing. The `date_captured` here is 2026-05-21; re-check if more than 30 days have elapsed.
2. **OpenAI gpt-image-1** — rates were not captured in this spike. Re-attempt via a logged-in browser session or from the OpenAI dashboard. Update this doc and `src/actual_cost_calculator.py` before Task 7 ships.
3. **Vertex AI Imagen** — out of scope for this spike. If the project ever switches to Vertex AI credentials, capture Vertex AI SKU pricing separately.
