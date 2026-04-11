---
name: catalog
description: List all available SmartArt layouts with their capacities, data shapes, and recommended use cases.
argument-hint: [--category CATEGORY] [--graphic-type TYPE]
allowed-tools: Bash(python *)
---

# /catalog

List available SmartArt layouts.

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

- **--category CATEGORY**: Filter by category (process, cycle, hierarchy, list, matrix, pyramid, relationship)
- **--graphic-type TYPE**: Show layouts for a specific graphic type (flowchart, cycle, org_chart, etc.)

## List Layouts

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.layouts.catalog import load_catalog, list_entries, get_layout_id_for_graphic_type

catalog = load_catalog()
entries = list_entries(v1_only=True)

for e in entries:
    print(f'{e[\"id\"]:20} {e.get(\"category\",\"\"):12} {e.get(\"data_shape\",\"\"):12} min={e.get(\"min_items\",\"?\")}-max={e.get(\"max_items\",\"?\")}')
"
```

Present the results as a formatted table:

| Layout ID | Category | Shape | Capacity | Use Case |
|-----------|----------|-------|----------|----------|

Include usage guidance: which graphic_type to pass, example items count.
