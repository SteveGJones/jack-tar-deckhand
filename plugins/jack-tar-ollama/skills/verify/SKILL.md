---
name: verify
description: Check Ollama availability, list installed image generation models, and report readiness status.
allowed-tools: Bash(curl *), Bash(ollama *)
---

# /verify

Check whether this plugin's prerequisites are met and report readiness.

## Step 1: Check Ollama is running

```bash
curl -s http://localhost:11434/api/tags 2>/dev/null | head -c 1
```

If the curl fails or returns empty, report:

```
PLUGIN: jack-tar-ollama
VERSION: 1.0.0

DEPENDENCIES:
  Ollama:          NOT_READY (Ollama is not running — start with 'ollama serve')

STATUS: NOT_AVAILABLE
REASON: Ollama is not running
```

## Step 2: List available image models

```bash
ollama list 2>/dev/null | grep '^x/' | awk '{print $1}'
```

Collect the list of `x/` prefixed models. These are image generation models.

## Step 3: Report status

If Ollama is running but no `x/` models are found:

```
PLUGIN: jack-tar-ollama
VERSION: 1.0.0

DEPENDENCIES:
  Ollama:          READY (running)

MODELS:
  (none found)     NOT_READY (no x/ image models installed — try 'ollama pull x/z-image-turbo')

STATUS: NOT_AVAILABLE
REASON: No image generation models installed
```

If Ollama is running and models are found, list each one:

```
PLUGIN: jack-tar-ollama
VERSION: 1.0.0

DEPENDENCIES:
  Ollama:          READY (running)

MODELS:
  x/z-image-turbo: READY
  x/flux2-klein:   READY

CAPABILITIES:
  image:           READY
  icon:            READY
  pattern:         READY
  diagram:         READY
  presentation:    READY

STATUS: FULLY_AVAILABLE
REASON: Ollama running with N image model(s) available
```
