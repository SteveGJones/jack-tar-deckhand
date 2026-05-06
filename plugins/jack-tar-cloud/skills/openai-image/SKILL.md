---
name: openai-image
description: Generate images using OpenAI GPT Image API. Requires OPENAI_API_KEY environment variable.
argument-hint: "a description of the image" [--output PATH] [--size SIZE] [--quality low|medium|high] [--background auto|transparent] [--model MODEL] [--resolution 1K]
allowed-tools: Bash(python *), Read, Glob
---

# /openai-image

Generate an image via OpenAI GPT Image API and report the file path with cost.

This skill wraps `src/generate_cloud_image.py`. It does NOT call APIs directly -- it delegates to the Python module which handles authentication, API calls, and file saving.

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
  echo "ERROR: jack-tar-cloud plugin not found."
  exit 1
fi
```

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Prompt**: The quoted text description of the image to generate
- **--output PATH**: Where to save the image (default: `output/openai-YYYYMMDD-HHMMSS.png`)
- **--size SIZE**: Image dimensions. Default: `1536x1024` (landscape). Options: `1024x1024`, `1536x1024`, `1024x1536`
- **--quality QUALITY**: Quality tier (`low`, `medium`, `high`). Default: `medium`
- **--background BG**: Background type (`auto`, `transparent`). Default: `auto`
- **--model MODEL**: Override model name (e.g., `gpt-image-1.5`)
- **--resolution RES**: Tier preset (`1K`, `2K`, `4K`). Default: `1K`. Note: gpt-image-1.5 supports `1K` only; passing `2K`/`4K` raises `ProviderResolutionUnsupportedError` with a recommendation to switch provider.

If no prompt is provided, stop and tell the user to provide a prompt.

## Check Provider Availability

Before generating, verify the provider is configured:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.provider_discovery import discover_providers
providers = discover_providers()
p = providers.get('openai', {})
print('available' if p.get('available') else 'not_configured')
"
```

If `not_configured`, tell the user to set `OPENAI_API_KEY` and stop.

## Generate the Image

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.generate_cloud_image import generate_cloud_image

result = generate_cloud_image(
    prompt='''$PROMPT''',
    provider='openai',
    output_path='$OUTPUT',
    size='$SIZE',
    quality='$QUALITY',
    background='$BACKGROUND',
    model='$MODEL',
    resolution='$RESOLUTION',
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

| Provider | Model | Quality | Size | Resolution tier | Cost |
|----------|-------|---------|------|-----------------|------|
| OpenAI | gpt-image-1.5 | low | 1024x1024 | 1K | $0.009 |
| OpenAI | gpt-image-1.5 | medium | 1024x1024 | 1K | $0.034 |
| OpenAI | gpt-image-1.5 | medium | 1536x1024 | 1K | $0.051 |
| OpenAI | gpt-image-1.5 | high | 1024x1024 | 1K | $0.133 |
| OpenAI | gpt-image-1.5 | high | 1536x1024 | 1K | $0.200 |

OpenAI does not support 2K or 4K resolution tiers; route to Google Nano Banana for those.

## Provider Status

Configured providers are detected at runtime via `src/provider_discovery.py`. Run `/jack-tar-cloud:verify` for the current state of all configured providers.
