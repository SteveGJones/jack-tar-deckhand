---
name: inject
description: Post-process an assembled deck — graft SmartArt from carrier files into the host .pptx. Reads smartart-spec.json from the deck directory to find carrier files and target slides.
argument-hint: --deck-dir PATH
allowed-tools: Bash(python *)
---

# /inject

Graft editable SmartArt diagrams into an assembled PowerPoint deck. This skill runs AFTER the deck assembler has produced a .pptx. It reads the SmartArtSpec to find which slides need SmartArt injected and performs the OOXML surgery.

## Locate Plugin

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_MSFT_SMARTART_ROOT'):
    print(os.environ['JACK_TAR_MSFT_SMARTART_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-msft-smartart/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-msft-smartart'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then echo "ERROR: jack-tar-msft-smartart not found" && exit 1; fi
```

## Parse Arguments

- **--deck-dir PATH**: DeckContext directory containing the assembled .pptx and smartart-spec.json (default: `./tmp/deck/`)

## Run Injection

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.pipeline import run_injection_step, format_delivery_message

deck_dir = '$DECK_DIR'
result = run_injection_step(deck_dir)
print(json.dumps(result, indent=2))
"
```

If the result shows `injected > 0` slides, report success. If `skipped > 0`, explain which slides were skipped and why.

## Delivery Report

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.pipeline import format_delivery_message
msg = format_delivery_message('$DECK_DIR')
print(msg)
"
```

Display the speaker-facing delivery message.
