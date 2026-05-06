---
name: image
description: Smart router — generates an image using the best available cloud provider. Tries providers in priority order: FAL (FLUX), OpenAI (GPT Image), Google (Imagen). Requires at least one provider configured.
argument-hint: "a description of the image" [--output PATH] [--size WxH] [--quality low|medium|high] [--provider openai|google|fal] [--model MODEL] [--resolution 1K|2K|4K]
allowed-tools: Bash(python *), Skill
---

# /image

Generate an image using the best available cloud provider.

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
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then echo "ERROR: jack-tar-cloud not found" && exit 1; fi
```

## Parse Arguments

Parse `$ARGUMENTS` for:
- **Prompt**: The quoted description
- **--output PATH**: Where to save
- **--size SIZE**: Dimensions (default: `1536x1024`)
- **--model MODEL**: Specific model ID (passed through to the provider skill)
- **--provider PROVIDER**: Force a specific provider instead of auto-routing
- **--resolution RES**: Tier (`1K`, `2K`, `4K`). Default: `1K`. Forwarded to the chosen per-provider skill. Provider must support the requested tier — see EPIC #58 capability matrix.

## Discover Available Providers

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import os, json
providers = {}
providers['openai'] = bool(os.environ.get('OPENAI_API_KEY'))
providers['google'] = bool(os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GOOGLE_API_KEY'))
providers['fal'] = bool(os.environ.get('FAL_KEY'))
print(json.dumps(providers))
"
```

Parse the JSON. If `--provider` was specified, check that provider is available. If no providers are available, report NOT_AVAILABLE and tell the user to run `/jack-tar-cloud:verify` for setup instructions.

## Select Provider and Route

If `--provider` is specified and available, use it directly.

Otherwise, route based on content suitability:

1. **Text-heavy content** (slides with visible text, labels, diagrams) → prefer Google Nano Banana (best text rendering), then OpenAI, then FAL
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

**Resolution-aware routing:** when `--resolution 4K` is requested, restrict to providers that support it (Google Nano Banana Pro/Flash). When `--resolution 2K`, restrict to Google (Imagen Standard, Nano Banana Pro/Flash) or FAL FLUX 2 Pro. When `--resolution 1K` (default), all available providers are eligible.

Forward the flag to the dispatched per-provider skill:
- `--resolution 1K` (or omitted) → no change to existing routing
- `--resolution 2K` → fal-image (FLUX 2 Pro) or google-image (Imagen Standard / Nano Banana Pro)
- `--resolution 4K` → google-image with `--model gemini-3.1-flash-image-preview` (Flash 4K, $0.151) or `--model gemini-3-pro-image-preview` (Pro 4K, $0.240)

Pass through all arguments (--output, --size, --model, --resolution, original prompt).

If the first provider fails, try the next available provider in the priority order.
