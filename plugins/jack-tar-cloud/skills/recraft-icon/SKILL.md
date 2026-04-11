---
name: recraft-icon
description: Generate vector icons (SVG) using Recraft V4 API (direct or via FAL.ai). Accepts a text prompt with optional brand colors, generates native SVG output, and saves to a path. Requires OPENAI_API_KEY (Recraft direct) or FAL_KEY (FAL.ai route).
argument-hint: "icon description" [--provider recraft|fal] [--output PATH] [--colors HEX,HEX,...] [--format svg|png] [--tier standard|pro]
allowed-tools: Bash(python *), Read, Glob
---

# /recraft-icon

Generate a vector icon (SVG) via a cloud API and report the file path with cost.

This skill wraps `src/generate_cloud_icon.py`. Recraft V4 is the ONLY model that produces native SVG output -- this is why icons always route to cloud even in draft mode.

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
- **Description**: The quoted text describing the icon to generate
- **--provider PROVIDER**: Cloud provider (`recraft`, `fal`). Default: `recraft`
- **--output PATH**: Where to save the icon (default: `output/icon-YYYYMMDD-HHMMSS.svg`)
- **--colors COLORS**: Comma-separated hex colours for brand palette (e.g., `003366,FFCC00,F5F5F5`)
- **--format FORMAT**: Output format (`svg` default, `png`). SVG strongly preferred for icons.
- **--tier TIER**: Quality tier (`standard`, `pro`). Default: `standard`

If no description is provided, stop and tell the user what they need to provide.

## Parse Brand Colors

If `--colors` is provided, convert hex values to RGB dicts for the API:

```python
colors_hex = "$COLORS".split(",")
colors_rgb = [
    {"r": int(h[0:2], 16), "g": int(h[2:4], 16), "b": int(h[4:6], 16)}
    for h in colors_hex
]
```

## Check Provider Availability

Before generating, verify the provider is configured:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.provider_discovery import discover_providers
providers = discover_providers()
provider = '$PROVIDER'
if provider == 'recraft':
    p = providers.get('recraft', {})
    env_var = 'RECRAFT_API'
else:
    p = providers.get('fal', {})
    env_var = 'FAL_KEY'
print('available' if p.get('available') else f'not_configured: set {env_var}')
"
```

If not configured, tell the user which environment variable to set:
- `recraft` needs `RECRAFT_API` (see research/04-cloud-api-setup-licensing.md section D)
- `fal` needs `FAL_KEY` (see research/04-cloud-api-setup-licensing.md section C)

## Generate the Icon

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.generate_cloud_icon import generate_cloud_icon

result = generate_cloud_icon(
    prompt='''$PROMPT''',
    provider='$PROVIDER',
    output_path='$OUTPUT',
    colors=$COLORS_RGB,
    output_format='$FORMAT',
    tier='$TIER',
)
print(json.dumps(result, indent=2))
"
```

## Report Results

Report to the user:
- **File path**: The saved icon location
- **Format**: SVG or PNG
- **Provider**: Which API was used
- **Cost**: Estimated USD cost
- **Status**: generated, failed, etc.

## Icon Prompt Engineering

For best results with Recraft V4:
- Focus on form and clarity, not photorealistic detail
- Specify stroke weight: "consistent 2px stroke weight"
- Use the `--colors` parameter for brand consistency
- Keep designs simple -- icons must be recognizable at small sizes
- Use `vector_illustration` style for flat icons, `icon` style for app icons

## Cost Reference

| Provider | Tier | Format | Cost |
|----------|------|--------|------|
| Recraft Direct | standard | SVG | $0.08 |
| Recraft Direct | pro | SVG | $0.30 |
| FAL.ai Recraft | standard | SVG | $0.08 |
| FAL.ai Recraft | pro | SVG | $0.30 |
| Recraft Direct | standard | PNG | $0.04 |
| Recraft Direct | pro | PNG | $0.25 |

## Provider Status

Currently neither Recraft nor FAL.ai is configured. Both provider functions are stubbed with clear error messages pointing to setup documentation.
