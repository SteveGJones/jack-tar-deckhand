---
name: recraft-image
description: Generate raster images using Recraft V4 (1K standard, 2K Pro, 4K via Creative Upscale). Brand-color-fidelity provider — best for slides where exact hex compliance matters more than photorealistic detail. Requires RECRAFT_API_KEY (direct) or FAL_KEY (via FAL).
argument-hint: "image description" [--output PATH] [--tier standard|pro] [--resolution 1K|2K|4K] [--colors HEX,HEX,...] [--style realistic_image|digital_illustration|vector_illustration]
allowed-tools: Bash(python *), Read, Glob
---

# /recraft-image

Generate a raster image via Recraft V4 and report the file path with cost.

This skill wraps `src/generate_cloud_image.py:generate_recraft_*`. Recraft V4 is the brand-color-fidelity raster lane (best when palette has 3+ specified hexes; outperforms FLUX and Nano Banana on exact hex compliance).

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
  echo "ERROR: jack-tar-cloud plugin not found." && exit 1
fi
```

## Parse Arguments

- **Description**: quoted text describing the image
- **--output PATH**: Where to save (default `output/recraft-YYYYMMDD-HHMMSS.png`)
- **--tier TIER**: `standard` (1024², $0.04) or `pro` (2048², $0.25). Default `pro`.
- **--resolution RES**: `1K`, `2K`, `4K`. Default `2K`. Tier+resolution must match capability:
  - `standard` → 1K only
  - `pro` → 2K, 4K (4K is 2K + Creative Upscale, ~$0.50 total)

  Unsupported combinations raise `ProviderResolutionUnsupportedError` with the supported tier list.
- **--colors COLORS**: Comma-separated hex (e.g. `003366,FFCC00,F5F5F5`). Forwarded as RGB control dicts to Recraft's brand-color preservation.
- **--style STYLE**: Recraft style — `realistic_image` (default), `digital_illustration`, `vector_illustration`. Direct API only; FAL ignores style.

## Check Provider Availability

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import os
direct = bool(os.environ.get('RECRAFT_API_KEY') or os.environ.get('RECRAFT_API'))
fal = bool(os.environ.get('FAL_KEY'))
print('available' if (direct or fal) else 'not_configured')
"
```

If `not_configured`, tell the user to set `RECRAFT_API_KEY` (direct API, preferred) or `FAL_KEY` (via FAL) and stop.

## Generate

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.generate_cloud_image import generate_cloud_image

colors_hex = '$COLORS'.split(',') if '$COLORS' else None
colors_rgb = (
    [{'rgb': [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)]} for h in colors_hex]
    if colors_hex else None
)

result = generate_cloud_image(
    prompt='''$PROMPT''',
    provider='recraft',
    output_path='$OUTPUT',
    tier='$TIER',
    resolution='$RESOLUTION',
    colors=colors_rgb,
    style='$STYLE',
)
print(json.dumps(result, indent=2))
"
```

## Report Results

Report to the user:
- **File path**: The saved image location
- **Provider/route**: `recraft` (direct API) or `fal-recraft` (via FAL)
- **Tier / Resolution**: which combination ran
- **Cost**: Estimated USD cost
- **Status**: generated, failed, etc.

If generation fails, surface the error message. For `ProviderResolutionUnsupportedError`, the message lists the supported tier list so the speaker can retry with a valid combination.

## Cost Reference

| Tier | Resolution | Cost | Output |
|---|---|---|---|
| standard | 1K | $0.04 | 1024² |
| pro | 2K | $0.25 | 2048² |
| pro | 4K | $0.50 | up to 4096² (chain: 2K Pro + Creative Upscale) |

**vs Nano Banana Pro 4K ($0.24):** Recraft 4K is ~2× the cost. Choose Recraft when brand-color fidelity is critical (logos, product shots, brand-led hero slides with 3+ specified hexes); choose Nano Banana Pro when photorealistic detail matters more.

The 4K Creative Upscale price is parity-assumed at $0.25 (FAL confirmed; direct API price not surfaced in public docs). Override via `RECRAFT_UPSCALE_COST_USD` env var if the actual figure differs.
