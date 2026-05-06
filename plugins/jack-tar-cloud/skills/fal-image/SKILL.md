---
name: fal-image
description: Generate images using FAL.ai FLUX API. Requires FAL_KEY environment variable.
argument-hint: "a description of the image" [--output PATH] [--size WxH] [--model MODEL] [--resolution 1K|2K]
allowed-tools: Bash(python *)
---

# /fal-image

Generate an image via FAL.ai FLUX API.

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
- **--output PATH**: Where to save (default: `output/fal-YYYYMMDD-HHMMSS.png`)
- **--size WxH**: Explicit pixel dimensions (e.g. `1920x1080` or `2048x2048`). Translated to FAL `image_size={"width":W, "height":H}`. If both `--size` and `--resolution` are passed, `--size` wins and a warning is logged. If omitted, `--resolution` selects a sensible preset.
- **--model MODEL**: FAL endpoint (default: `fal-ai/flux-2-pro`). Other options: `fal-ai/flux-2-klein`, `fal-ai/ideogram/v3`.
- **--resolution RES**: Tier (`1K`, `2K`). Default: `1K`. FLUX 2 Pro supports both; Klein and Ideogram support 1K only. Unsupported model/resolution combinations raise `ProviderResolutionUnsupportedError`; the exception message lists supported tiers.

## Check Availability

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import os
configured = bool(os.environ.get('FAL_KEY'))
print('available' if configured else 'not_configured')
"
```

If `not_configured`, tell the user to set `FAL_KEY` and stop.

## Generate

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.generate_cloud_image import generate_cloud_image

kwargs = dict(
    prompt='$PROMPT',
    provider='fal',
    output_path='$OUTPUT_PATH',
    model='$MODEL',
    resolution='$RESOLUTION',
)

# --size 1920x1080 translates to image_size dict (FAL's native parameter form).
size = '$SIZE'
if size and 'x' in size:
    w, h = size.split('x')
    kwargs['image_size'] = {'width': int(w), 'height': int(h)}

result = generate_cloud_image(**kwargs)
print(json.dumps(result, indent=2))
"
```

If successful, report the file path and cost.
If failed, report the error.

## Cost Reference

| Model | 1K (1MP) | 2K (~4.2MP) | Notes |
|---|---|---|---|
| fal-ai/flux-2-pro | $0.030 | $0.078 | tiered: $0.030 first MP + $0.015/extra MP (2048² is ~4.19 MP) |
| fal-ai/flux-2-klein | $0.014 | n/a | flat |
| fal-ai/ideogram/v3 | $0.060 | n/a | flat |
