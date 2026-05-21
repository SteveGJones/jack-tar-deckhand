# Phase 0 — SDK Usage Field Discovery

**Spike:** Actual-token pricing vs catalog estimates for image generation APIs
**Task:** 2 of 22
**Date captured:** 2026-05-21
**SDK versions tested:** `google-genai 1.69.0`, `openai 2.30.0`

---

## Google Nano Banana — `gemini-3.1-flash-image-preview` / `gemini-3-pro-image-preview`

- **SDK call:** `client.models.generate_content(model="gemini-3.1-flash-image-preview", contents=[prompt], config=types.GenerateContentConfig(response_modalities=["IMAGE"], image_config=types.ImageConfig(image_size="1K")))`
- **Response object type:** `google.genai.types.GenerateContentResponse`
- **Usage field path:** `response.usage_metadata`
- **Fields inside usage object** (`google.genai.types.GenerateContentResponseUsageMetadata`):
  - `prompt_token_count: int | None`
  - `candidates_token_count: int | None`
  - `total_token_count: int | None`
  - `cached_content_token_count: int | None`
  - `thoughts_token_count: int | None`
  - `tool_use_prompt_token_count: int | None`
  - `traffic_type: TrafficType | None` — enum: `ON_DEMAND`, `ON_DEMAND_PRIORITY`, `ON_DEMAND_FLEX`, `PROVISIONED_THROUGHPUT`
  - `cache_tokens_details: list[ModalityTokenCount] | None`
  - `candidates_tokens_details: list[ModalityTokenCount] | None`
  - `prompt_tokens_details: list[ModalityTokenCount] | None`
  - `tool_use_prompt_tokens_details: list[ModalityTokenCount] | None`
- **`ModalityTokenCount` sub-type fields:**
  - `modality: MediaModality | None` — enum: `TEXT`, `IMAGE`, `VIDEO`, `AUDIO`, `DOCUMENT`
  - `token_count: int | None`
- **SDK version tested:** `google-genai 1.69.0`
- **Date captured:** 2026-05-21
- **Notes:**
  - Both Flash and Pro models (`gemini-3.1-flash-image-preview`, `gemini-3-pro-image-preview`) use the `generate_content` API path and return `GenerateContentResponse`. One doc entry covers both model IDs.
  - The `candidates_tokens_details` list with `modality=IMAGE` should carry the image output token count — this is the field that enables actual cost computation per-image vs catalog flat rates.
  - `prompt_tokens_details` with `modality=TEXT` carries input text token count.
  - `total_token_count` is the sum but does not break down by modality — use the `*_tokens_details` lists for modality-level precision.
  - The type for this field is `GenerateContentResponseUsageMetadata` (note: distinct from the live-session `UsageMetadata` type also present in the SDK, and from `CachedContentUsageMetadata`).

---

## Google Imagen — `imagen-4.0-generate-001` / `imagen-4.0-fast-generate-001`

- **SDK call:** `client.models.generate_images(model="imagen-4.0-generate-001", prompt=prompt, config=types.GenerateImagesConfig(image_size="1K"))` (Imagen Fast omits `image_size`)
- **Response object type:** `google.genai.types.GenerateImagesResponse`
- **Usage field path:** `none — defer from refactor`
- **Fields inside usage object:** N/A — `GenerateImagesResponse` has no usage field
- **SDK version tested:** `google-genai 1.69.0`
- **Date captured:** 2026-05-21
- **Notes:**
  - `GenerateImagesResponse` has exactly three fields: `sdk_http_response`, `generated_images`, `positive_prompt_safety_attributes`. No usage/token field present.
  - Confirmed by both inspecting `types.GenerateImagesResponse.model_fields` and reading the `generate_images` method source — the return type annotation is `GenerateImagesResponse` with no usage surface.
  - **Downstream impact:** Task 6 (Imagen actual-cost path) is SKIPPED. Imagen billing remains catalog-only (flat per-image rate: Fast $0.020, Standard $0.040 per image at 1K).

---

## OpenAI — `gpt-image-1` via `images.generate`

- **SDK call:** `client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024", quality="medium", n=1)`
- **Response object type:** `openai.types.images_response.ImagesResponse`
- **Usage field path:** `response.usage`
- **Fields inside usage object** (`openai.types.images_response.Usage`):
  - `input_tokens: int`
  - `output_tokens: int`
  - `total_tokens: int`
  - `input_tokens_details: UsageInputTokensDetails`
    - `image_tokens: int`
    - `text_tokens: int`
  - `output_tokens_details: UsageOutputTokensDetails | None`
    - `image_tokens: int`
    - `text_tokens: int`
- **SDK version tested:** `openai 2.30.0`
- **Date captured:** 2026-05-21
- **Notes:**
  - `usage` is an optional field on `ImagesResponse` (`Union[Usage, None]`, default `None`). The API must be asked to return it — verify in Phase 1 whether it populates by default or requires a request flag.
  - `input_tokens_details.image_tokens` will be non-zero when an input image is provided (edits/variations); for a plain `images.generate` call with text-only prompt, expect `image_tokens=0` and `text_tokens=N`.
  - `output_tokens` / `output_tokens_details.image_tokens` is the key field for actual cost — maps to OpenAI's per-output-token pricing for gpt-image-1 ($0.04/1M input, $0.04/1M output as of 2026-05-21 public pricing).
  - Both `input_tokens_details` and `output_tokens_details` are present as typed Pydantic models (not just dicts), making them safe to access by attribute.
  - **Downstream impact:** Task 7 (OpenAI actual-cost path) PROCEEDS.

---

## Summary Table

| Provider | Model(s) | Usage Field Path | Proceed to Actual-Cost Task? |
|----------|----------|-----------------|------------------------------|
| Google Nano Banana | `gemini-3.1-flash-image-preview`, `gemini-3-pro-image-preview` | `response.usage_metadata` | YES — Tasks 5, 12, 19 |
| Google Imagen | `imagen-4.0-generate-001`, `imagen-4.0-fast-generate-001` | absent — defer from refactor | NO — Task 6 SKIPPED, catalog-only |
| OpenAI | `gpt-image-1` | `response.usage` | YES — Task 7 |

---

## Open Questions for Phase 1

1. **Google Nano Banana — which token fields map to image cost?** The Gemini Developer API pricing page states image generation pricing is per-image (not per-token for image output). Need to confirm in Phase 1 whether `candidates_token_count` actually reflects the image-output billing unit, or whether the catalog flat rate already captures actual cost and `usage_metadata` is informational only for text tokens.

2. **OpenAI — does `usage` populate without a flag?** The field is `Optional[Usage]` (default `None`). Phase 1 live-call validation must confirm that `response.usage` is non-None on a real `images.generate` response.

3. **Google Nano Banana — `total_token_count` vs modality details?** For actual cost computation, should Phase 2 use `total_token_count` (simpler) or `prompt_tokens_details` + `candidates_tokens_details` filtered by modality (more precise)? Recommend the latter if image-token pricing differs from text-token pricing for the model.
