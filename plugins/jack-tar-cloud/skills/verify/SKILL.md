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
  Nanobanana Flash:    gemini-3.1-flash-image     $0.067/image  (best text rendering)
  Nanobanana Pro:      gemini-3-pro-image          $0.134/image  (premium quality)
  Imagen Fast:         imagen-4.0-fast-generate-001        $0.020/image  (budget bulk)
  Imagen Standard:     imagen-4.0-generate-001             $0.040/image  (standard quality)

CAPABILITIES:
  image:           READY (3/4 providers available)
  icon:            READY (recraft available)

STATUS: PARTIALLY_AVAILABLE
REASON: All providers configured
```

## Step 4: Model catalog staleness hint (non-blocking)

Report which model catalog is in effect and how old the local cache is:

```bash
python3 - << 'PYEOF'
import sys
sys.path.insert(0, "PLUGIN_ROOT")  # replace with the plugin root path
from src.model_catalog_refresh import staleness_report
report = staleness_report()
print("MODEL CATALOG:")
print(f"  version:  {report['version']} (data updated {report['updated']})")
print(f"  source:   {report['source']}")
if "cache_age_days" in report:
    print(f"  cache age: {report['cache_age_days']} days")
    if report["cache_age_days"] > 30:
        print("  hint: cache is over a month old — run /jack-tar-cloud:refresh-models")
else:
    print("  hint: running on the shipped baseline — /jack-tar-cloud:refresh-models fetches the latest")
PYEOF
```

This never blocks verification — model ids and prices move faster than
plugin releases (EPIC #125), so the hint just tells the operator when a
refresh is worth running.

## Step 5 (optional, on request): live model probe

When the operator asks to "check the models", "find the latest models", or
after any 404/NOT_FOUND from a provider, run the live discovery probe. It
asks each probeable provider (Google, OpenAI, Ollama) what it serves RIGHT
NOW and classifies every catalog entry:

```bash
python3 - << 'PYEOF'
import json, sys
sys.path.insert(0, "PLUGIN_ROOT")  # replace with the plugin root path
from src.model_probe import probe_report
report = probe_report()
print(json.dumps(report, indent=2))
PYEOF
```

Present the results as:

- **suspect_retired** entries — lead with these: the catalog thinks the
  model is active but the provider no longer lists it. Recommend
  `/jack-tar-cloud:refresh-models` (a corrected catalog may already be
  published) or a local-config override.
- **new_candidates** — upstream models no catalog entry covers. These are
  NOT routable: existence is provable, price is not, and the budget
  tracker cannot cost an uncataloged model. Offer them as candidates the
  operator can add via a `model_catalog` override in `local-config.json`
  (explicit opt-in) or propose for the canonical catalog.
- **unprobed** — FAL/Recraft have no list API; entries with no configured
  credentials are skipped with the reason shown. Never treat unprobed as
  a failure.
