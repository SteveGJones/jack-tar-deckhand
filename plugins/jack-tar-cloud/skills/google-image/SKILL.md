---
name: google-image
description: Generate images using Google Gemini/Imagen API. Requires GOOGLE_CLOUD_PROJECT environment variable.
argument-hint: "a description of the image" [--output PATH] [--size SIZE] [--quality low|medium|high]
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
- **--size SIZE**: Dimensions (default: `1536x1024`)
- **--quality QUALITY**: `low`, `medium`, or `high` (default: `medium`)

## Check Availability

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import os
configured = bool(os.environ.get('GOOGLE_CLOUD_PROJECT'))
print('available' if configured else 'not_configured')
"
```

If `not_configured`, tell the user to set `GOOGLE_CLOUD_PROJECT` and stop.

## Generate

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.generate_cloud_image import generate_cloud_image
result = generate_cloud_image(
    prompt='$PROMPT',
    provider='google_vertex',
    output_path='$OUTPUT_PATH',
    size='$SIZE',
    quality='$QUALITY',
)
print(json.dumps(result, indent=2))
"
```

If successful, report the file path and cost.
If failed, report the error.
