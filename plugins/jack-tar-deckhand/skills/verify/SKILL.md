---
name: verify
description: Meta-verify — discover all jack-tar engine plugins, call each verify, report aggregate pipeline capability.
allowed-tools: Bash(python *), Bash(node *), Skill
---

# /verify

Discover all installed jack-tar engine plugins, call each plugin's `:verify` skill, and report aggregate pipeline capability.

## Step 1: Check local dependencies

Check that Python and Node.js with pptxgenjs are available:

```bash
python3 --version
node -e "require('pptxgenjs'); console.log('pptxgenjs OK')" 2>/dev/null || echo "pptxgenjs NOT_FOUND"
```

## Step 2: Discover engine plugins

Call each engine plugin's verify skill. If the skill doesn't exist (plugin not installed), record as "Not installed".

Invoke each in sequence:
1. `jack-tar-ollama:verify`
2. `jack-tar-cloud:verify`
3. `jack-tar-msft-smartart:verify`
4. `jack-tar-custom-smartart:verify`

For each, extract the STATUS line from the output.

## Step 3: Determine pipeline capabilities

Based on engine plugin availability:
- **Draft images:** READY if jack-tar-ollama is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Production images:** READY if jack-tar-cloud is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Editable SmartArt:** READY if jack-tar-msft-smartart is FULLY_AVAILABLE
- **Custom graphics:** READY if jack-tar-custom-smartart is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Deck assembly:** READY if pptxgenjs is installed
- **QA checks:** always READY (built into this plugin)

## Step 4: Report status

Example output:

```
PLUGIN: jack-tar-deckhand
VERSION: 1.0.0

DEPENDENCIES:
  Python:          READY (3.12.x)
  Node.js:         READY (22.x)
  pptxgenjs:       READY

ENGINE PLUGINS:
  jack-tar-ollama:           FULLY_AVAILABLE
  jack-tar-cloud:            PARTIALLY_AVAILABLE
  jack-tar-msft-smartart:    FULLY_AVAILABLE
  jack-tar-custom-smartart:  NOT_AVAILABLE

PIPELINE CAPABILITY:
  Draft images:      READY (ollama available)
  Production images: READY (cloud partially available)
  Editable SmartArt: READY (msft-smartart available)
  Custom graphics:   NOT_READY (custom-smartart not available)
  Deck assembly:     READY (pptxgenjs installed)
  QA checks:         READY

STATUS: PARTIALLY_AVAILABLE
REASON: jack-tar-custom-smartart not available
```

Overall STATUS rules:
- `STATUS: FULLY_AVAILABLE` — pptxgenjs installed + at least one image plugin + at least one SmartArt plugin
- `STATUS: PARTIALLY_AVAILABLE` — pptxgenjs installed but some engine plugins missing
- `STATUS: NOT_AVAILABLE` — pptxgenjs not installed (can't assemble decks at all)
