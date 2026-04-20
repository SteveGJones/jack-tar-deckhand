---
name: verify
description: Check which cloud image providers are configured and report readiness status.
allowed-tools: Bash(python *)
---

# /verify

Check whether this plugin's prerequisites are met and report per-provider readiness.

## Step 1: Check Python dependencies

```bash
python3 -c "
missing = []
try:
    import requests
except ImportError:
    missing.append('requests')
try:
    import openai
except ImportError:
    missing.append('openai')
try:
    from google import genai
except ImportError:
    missing.append('google-genai')
try:
    import fal_client
except ImportError:
    missing.append('fal-client')
if missing:
    print('MISSING:' + ','.join(missing))
else:
    print('ALL_PRESENT')
"
```

If any packages are missing, report NOT_AVAILABLE with install instructions (`pip install <package>`).

## Step 2: Check provider API keys

```bash
python3 -c "
import os
providers = {
    'openai': bool(os.environ.get('OPENAI_API_KEY')),
    'google': bool(os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GOOGLE_API_KEY')),
    'fal': bool(os.environ.get('FAL_KEY')),
}
# Recraft uses OPENAI_API_KEY
providers['recraft'] = providers['openai']
import json
print(json.dumps(providers))
"
```

## Step 3: Report status

Count ready providers and report one of:
- `STATUS: FULLY_AVAILABLE` — all dependencies present and at least 2 providers configured
- `STATUS: PARTIALLY_AVAILABLE` — dependencies present but only 1-3 providers configured
- `STATUS: NOT_AVAILABLE` — missing Python dependencies or zero providers configured

Example output:

```
PLUGIN: jack-tar-cloud
VERSION: 1.0.0

DEPENDENCIES:
  Python:          READY (3.12.x)
  requests:        READY
  openai:          READY
  google-genai:    READY
  fal-client:      READY

PROVIDERS:
  openai:              READY (OPENAI_API_KEY set)
  google-nanobanana:   READY (Flash + Pro via GOOGLE_API_KEY)
  google-imagen:       READY (Fast + Standard via GOOGLE_API_KEY)
  fal:                 READY (FAL_KEY set)
  recraft:             READY (uses OPENAI_API_KEY)

GOOGLE TIERS:
  Nanobanana Flash:    gemini-3.1-flash-image-preview     $0.067/image  (best text rendering)
  Nanobanana Pro:      gemini-3-pro-image-preview          $0.134/image  (premium quality)
  Imagen Fast:         imagen-4.0-fast-generate-001        $0.020/image  (budget bulk)
  Imagen Standard:     imagen-4.0-generate-001             $0.040/image  (standard quality)

CAPABILITIES:
  image:           READY (3/4 providers available)
  icon:            READY (recraft available)

STATUS: PARTIALLY_AVAILABLE
REASON: All providers configured
```
