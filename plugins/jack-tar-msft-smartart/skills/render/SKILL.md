---
name: render
description: Generate an editable SmartArt carrier .pptx from a spec. Accepts a SmartArt spec (graphic_type, items or tree, layout_id), renders the carrier file, and returns the path.
argument-hint: --spec-file PATH | --graphic-type TYPE --items "item1;item2;item3" [--layout-id ID] [--output-dir DIR]
allowed-tools: Bash(python *)
---

# /render

Generate an editable SmartArt carrier .pptx from a structured spec.

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

Parse `$ARGUMENTS`:
- **--spec-file PATH**: Path to a JSON file containing a complete SmartArt spec
- **--graphic-type TYPE**: SmartArt graphic type (e.g., `flowchart`, `cycle`, `org_chart`, `list`)
- **--items "item1;item2"**: Semicolon-separated items for flat-list layouts
- **--layout-id ID**: Specific layout ID (e.g., `process1`, `cycle2`). Optional — will use default for the graphic type.
- **--output-dir DIR**: Directory to write carrier file (default: `./tmp/smartart/`)

If `--spec-file` is provided, read it as the spec. Otherwise build a spec from `--graphic-type` and `--items`.

## Build Spec

If building from arguments, construct:
```json
{
  "graphic_type": "<TYPE>",
  "layout_id": "<LAYOUT_ID or null>",
  "items": ["<item1>", "<item2>"]
}
```

For hierarchical types (org_chart, hierarchy), `--items` is not valid — require `--spec-file` with a `tree` key.

## Render Carrier

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json, sys
from pathlib import Path

spec = $SPEC_DICT
output_dir = '$OUTPUT_DIR'
Path(output_dir).mkdir(parents=True, exist_ok=True)

from src.engine import render
result = render(spec, output_dir)
print(json.dumps(result, indent=2))
"
```

The `render()` function returns a dict with at minimum:
- `carrier_pptx`: absolute path to the generated carrier file
- `layout_id`: the layout that was used
- `status`: `ok` or `error`

## Report

Report the carrier file path, layout used, and status. On error, report the error message.
