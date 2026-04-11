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
    'google': bool(os.environ.get('GOOGLE_CLOUD_PROJECT')),
    'fal': bool(os.environ.get('FAL_KEY')),
}
# Recraft uses OPENAI_API_KEY
providers['recraft'] = providers['openai']
import json
print(json.dumps(providers))
"
```

## Step 3: Report status

Count ready providers. If 0, status is NOT_AVAILABLE. If some but not all, PARTIALLY_AVAILABLE. If all, FULLY_AVAILABLE.

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
  openai:          READY (OPENAI_API_KEY set)
  google:          NOT_READY (GOOGLE_CLOUD_PROJECT not set)
  fal:             READY (FAL_KEY set)
  recraft:         READY (uses OPENAI_API_KEY)

CAPABILITIES:
  image:           READY (3/4 providers available)
  icon:            READY (recraft available)

STATUS: PARTIALLY_AVAILABLE
REASON: Google provider not configured (missing GOOGLE_CLOUD_PROJECT)
```
