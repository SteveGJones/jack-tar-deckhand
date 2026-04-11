---
name: cloud-generate-image
description: Generate images using cloud APIs (OpenAI GPT Image, Google Vertex Imagen, FAL.ai FLUX). Accepts a text prompt, generates via the specified provider, saves to a path, and returns the file path with cost metadata.
argument-hint: "a description of the image" [--provider openai|google_vertex|fal] [--output PATH] [--size SIZE] [--quality low|medium|high] [--background auto|transparent] [--model MODEL]
allowed-tools: Bash(python *), Read, Glob
---

# /cloud-generate-image

Generate an image via a cloud API provider and report the file path with cost.

This skill wraps `src/generate_cloud_image.py`. It does NOT call APIs directly -- it delegates to the Python module which handles authentication, API calls, and file saving.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Prompt**: The quoted text description of the image to generate
- **--provider PROVIDER**: Cloud provider to use (`openai`, `google_vertex`, `fal`). Default: `openai`
- **--output PATH**: Where to save the image (default: `output/cloud-YYYYMMDD-HHMMSS.png`)
- **--size SIZE**: Image dimensions. Default: `1536x1024` (landscape). Options: `1024x1024`, `1536x1024`, `1024x1536`
- **--quality QUALITY**: Quality tier (`low`, `medium`, `high`). Default: `medium`
- **--background BG**: Background type (`auto`, `transparent`). Default: `auto`
- **--model MODEL**: Override model name (provider-specific)

If no prompt is provided, stop and tell the user to provide a prompt.

## Check Provider Availability

Before generating, verify the provider is configured:

```bash
python3 -c "
from src.provider_discovery import discover_providers
providers = discover_providers()
p = providers.get('$PROVIDER', {})
print('available' if p.get('available') else 'not_configured')
"
```

If `not_configured`, tell the user which environment variable to set and reference `research/04-cloud-api-setup-licensing.md` for setup instructions:
- `openai` needs `OPENAI_API_KEY`
- `google_vertex` needs `GOOGLE_CLOUD_PROJECT`
- `fal` needs `FAL_KEY`

## Generate the Image

```bash
python3 -c "
import json
from src.generate_cloud_image import generate_cloud_image

result = generate_cloud_image(
    prompt='''$PROMPT''',
    provider='$PROVIDER',
    output_path='$OUTPUT',
    size='$SIZE',
    quality='$QUALITY',
    background='$BACKGROUND',
)
print(json.dumps(result, indent=2))
"
```

## Report Results

Report to the user:
- **File path**: The saved image location
- **Provider/model**: Which API and model was used
- **Cost**: Estimated USD cost of the generation
- **Status**: generated, failed, etc.

If the generation fails, show the error message. For `ProviderNotConfiguredError`, include the setup documentation reference.

## Cost Reference

| Provider | Model | Quality | Size | Cost |
|----------|-------|---------|------|------|
| OpenAI | gpt-image-1.5 | low | 1024x1024 | $0.009 |
| OpenAI | gpt-image-1.5 | medium | 1536x1024 | $0.051 |
| OpenAI | gpt-image-1.5 | high | 1536x1024 | $0.200 |
| Google | imagen-4-fast | - | any | $0.020 |
| Google | imagen-4-standard | - | any | $0.040 |
| FAL.ai | flux-2-pro | - | 1024x1024 | $0.030 |

## Provider Status

Configured providers are detected at runtime via `src/provider_discovery.py`. Currently:
- **OpenAI**: Available (gpt-image-1.5)
- **Google Vertex AI**: Not configured (stub)
- **FAL.ai**: Not configured (stub)
