---
name: icon
description: Smart router for vector icon generation. Tries Recraft V4 SVG first, falls back to OpenAI if unavailable.
argument-hint: "a description of the icon" [--output PATH] [--colors HEX,HEX] [--provider recraft|openai]
allowed-tools: Bash(python *), Skill
---

# /icon

Generate a vector icon using the best available cloud provider.

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

- **Prompt**: Description of the icon
- **--output PATH**: Where to save the output (SVG or PNG)
- **--colors HEX,HEX**: Brand colors as comma-separated hex values
- **--provider PROVIDER**: Force a provider (`recraft` or `openai`)

## Select Provider

Check if Recraft (OPENAI_API_KEY) is available. If yes and not forced otherwise, use Recraft -- it produces true SVG vectors. If Recraft unavailable, fall back to openai-image for raster output.

Dispatch:
- Recraft available → `/jack-tar-cloud:recraft-icon` with same arguments
- Recraft not available → `/jack-tar-cloud:openai-image` with same prompt (raster fallback, note to user)
