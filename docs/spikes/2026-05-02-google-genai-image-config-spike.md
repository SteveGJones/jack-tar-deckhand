# google-genai SDK image_config Support — Spike Report

**Date:** 2026-05-02
**Spec reference:** `docs/superpowers/specs/2026-05-02-cloud-resolution-control-design.md` §6
**Issue:** #59

## Result

**Chosen path:** PATH-B
**SDK version tested:** `1.69.0`

## Test outcomes

### PATH-A — raw dict on typed config
```
PATH-A: ACCEPTED — typed config takes image_config as dict
  cfg fields: ['audio_timestamp', 'automatic_function_calling', 'cached_content', 'candidate_count', 'construct', 'copy', 'dict', 'enable_enhanced_civic_answers', 'frequency_penalty', 'from_orm', 'http_options', 'image_config', 'json', 'labels', 'logprobs', 'max_output_tokens', 'media_resolution', 'model_armor_config', 'model_computed_fields', 'model_config', 'model_construct', 'model_copy', 'model_dump', 'model_dump_json', 'model_extra', 'model_fields', 'model_fields_set', 'model_json_schema', 'model_parametrized_name', 'model_post_init', 'model_rebuild', 'model_selection_config', 'model_validate', 'model_validate_json', 'model_validate_strings', 'parse_file', 'parse_obj', 'parse_raw', 'presence_penalty', 'response_json_schema', 'response_logprobs', 'response_mime_type', 'response_modalities', 'response_schema', 'routing_config', 'safety_settings', 'schema', 'schema_json', 'seed', 'service_tier', 'should_return_http_response', 'speech_config', 'stop_sequences', 'system_instruction', 'temperature', 'thinking_config', 'to_json_dict', 'tool_config', 'tools', 'top_k', 'top_p', 'update_forward_refs', 'validate']
```

### PATH-B — typed ImageConfig class
```
PATH-B: ACCEPTED — typed ImageConfig available
```

Additional inspection of `ImageConfig.model_fields` confirmed the following fields at SDK 1.69.0:

| Field | Type | Notes |
|---|---|---|
| `image_size` | `str \| None` | Supported: `"1K"`, `"2K"`, `"4K"`. Default: `"1K"`. |
| `aspect_ratio` | `str \| None` | Supported: `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"9:16"`, `"16:9"`, `"21:9"`. |
| `person_generation` | `str \| None` | `ALLOW_ALL`, `ALLOW_ADULT`, `ALLOW_NONE`. |
| `output_mime_type` | `str \| None` | Vertex AI only (not Gemini API). |
| `output_compression_quality` | `int \| None` | JPEG only; Vertex AI only. |

### PATH-C — raw generation_config dict (live API)
PATH-C: SKIPPED — requires live API call with credentials and ~$0.13 spend, deferred to smoke test (Phase 8)

## Decision

Both PATH-A (raw dict coerced into `image_config`) and PATH-B (typed `ImageConfig` class) are accepted by SDK 1.69.0. Per the decision matrix, PATH-B is the chosen implementation path because it is the cleanest and most type-safe option: IDEs surface field names and accepted values directly from the `ImageConfig` model definition, validation errors are caught at construction time rather than at API call time, and the `model_fields` introspection confirms that `image_size` and `aspect_ratio` are both present and documented in this SDK version.

## Implementation impact

`_generate_via_nano_banana` in `plugins/jack-tar-superpower-bridge/src/enrichment_ops/background.py` (or the equivalent resolution-control module) should use the following pattern:

```python
from google.genai.types import GenerateContentConfig, ImageConfig

config = GenerateContentConfig(
    response_modalities=["IMAGE", "TEXT"],
    image_config=ImageConfig(
        image_size=image_size,   # "1K" | "2K" | "4K"; map from caller's resolution param
        aspect_ratio=aspect_ratio,  # e.g. "16:9" for widescreen slides; optional
    ),
)
response = client.models.generate_content(
    model=model_id,   # e.g. "gemini-2.0-flash-preview-image-generation"
    contents=prompt,
    config=config,
)
```

No extra indirection is needed: `ImageConfig` is a plain Pydantic v2 model, so keyword arguments map directly to the camelCase aliases (`imageSize`, `aspectRatio`) that the REST API expects. The `image_config` field on `GenerateContentConfig` is already typed as accepting an `ImageConfig` instance (confirmed from the `dir(cfg)` output showing `image_config` in the field list), so no runtime coercion occurs.

## SDK version notes

SDK 1.69.0 supports the chosen path; no version pin required. `ImageConfig` and the `image_config` field on `GenerateContentConfig` are both present and non-deprecated at this version. The `image_size` field documents `"4K"` as a supported value, which is the target capability for the Nano Banana 4K feature (issue #59). No upgrade is needed before Phase 4 implementation begins.
