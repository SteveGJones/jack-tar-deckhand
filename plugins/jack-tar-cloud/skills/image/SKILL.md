---
name: image
description: Smart router — generates an image using the best available cloud provider. Tries providers in priority order: FAL (FLUX), OpenAI (GPT Image), Google (Imagen). Requires at least one provider configured.
argument-hint: "a description of the image" [--output PATH] [--size SIZE] [--quality low|medium|high] [--provider openai|google|fal]
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
- **--quality QUALITY**: `low`, `medium`, or `high` (default: `medium`)
- **--provider PROVIDER**: Force a specific provider instead of auto-routing

## Discover Available Providers

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import os, json
providers = {}
providers['openai'] = bool(os.environ.get('OPENAI_API_KEY'))
providers['google'] = bool(os.environ.get('GOOGLE_CLOUD_PROJECT'))
providers['fal'] = bool(os.environ.get('FAL_KEY'))
print(json.dumps(providers))
"
```

Parse the JSON. If `--provider` was specified, check that provider is available. If no providers are available, report NOT_AVAILABLE and tell the user to run `/jack-tar-cloud:verify` for setup instructions.

## Select Provider and Route

If `--provider` is specified and available, use it directly.

Otherwise, route in priority order: `fal` first (FLUX is best quality/cost), then `openai`, then `google`.

Dispatch the appropriate per-provider skill:
- `fal` → `/jack-tar-cloud:fal-image`
- `openai` → `/jack-tar-cloud:openai-image`
- `google` → `/jack-tar-cloud:google-image`

Pass through all arguments (--output, --size, --quality, original prompt).

If the first provider fails, try the next available provider.
