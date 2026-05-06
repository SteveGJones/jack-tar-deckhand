---
name: google-image
description: Generate images using Google Gemini/Imagen API. Requires GOOGLE_CLOUD_PROJECT environment variable.
argument-hint: "a description of the image" [--output PATH] [--aspect-ratio 16:9|1:1|4:3|9:16|3:4] [--model MODEL] [--tier draft|standard|premium] [--resolution 1K|2K|4K]
allowed-tools: Bash(python *)
---

# /google-image

Generate an image via Google Gemini/Imagen API.

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
- **--output PATH**: Where to save (default: `output/google-YYYYMMDD-HHMMSS.png`)
- **--aspect-ratio RATIO**: Image aspect ratio (`16:9`, `1:1`, `4:3`, `9:16`, `3:4`). Default: `16:9`. Imagen 4 honours this; Nano Banana ignores it (resolution alone determines output dimensions).
- **--resolution RES**: Tier (`1K`, `2K`, `4K`). Default: `1K`. Per-model support:
  - `imagen-4.0-fast-generate-001`: 1K only
  - `imagen-4.0-generate-001` / `imagen-4.0-ultra-generate-001`: 1K, 2K
  - `gemini-3.1-flash-image-preview`: 512, 1K, 2K, 4K
  - `gemini-3-pro-image-preview`: 1K, 2K, 4K
- **--model MODEL**: Specific Google model ID (overrides --tier)
- **--tier TIER**: Shorthand for model selection:
  - `draft` → `imagen-4.0-fast-generate-001` ($0.02)
  - `standard` → `gemini-3.1-flash-image-preview` ($0.067) — default
  - `premium` → `gemini-3-pro-image-preview` ($0.134)

If both `--model` and `--tier` are provided, `--model` takes precedence.
If neither is provided, defaults to `standard` tier (Nanobanana Flash).

## Check Availability

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import os
configured = bool(os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GOOGLE_API_KEY'))
print('available' if configured else 'not_configured')
"
```

If `not_configured`, tell the user to set `GOOGLE_API_KEY` (or `GOOGLE_CLOUD_PROJECT`) and stop.

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
    aspect_ratio='$ASPECT_RATIO',
    resolution='$RESOLUTION',
)
print(json.dumps(result, indent=2))
"
```

If successful, report the file path, model used, and cost.
If failed, report the error.

## Cost Reference

| Model | 512 | 1K | 2K | 4K |
|---|---|---|---|---|
| imagen-4.0-fast-generate-001 (Vertex) | — | $0.020 | n/a | n/a |
| imagen-4.0-generate-001 (Vertex) | — | $0.040 | $0.040 | n/a |
| imagen-4.0-generate-001 (Dev API) | — | $0.040 | $0.101 | n/a |
| imagen-4.0-ultra-generate-001 (Vertex) | — | $0.060 | $0.060 | n/a |
| gemini-3.1-flash-image-preview | $0.045 | $0.067 | $0.101 | $0.151 |
| gemini-3-pro-image-preview | — | $0.134 | $0.134 | $0.240 |

Imagen pricing depends on backend: `GOOGLE_APPLICATION_CREDENTIALS` set → Vertex AI flat per-image; `GOOGLE_API_KEY` only → Gemini Developer API token-based.
