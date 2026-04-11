---
name: render
description: Render a SmartArt graphic to PNG using SVG, Mermaid, Vega-Lite, or matplotlib. Accepts a structured spec and produces a rasterised PNG.
argument-hint: --spec-file PATH | --graphic-type TYPE --items "item1;item2" [--output PATH] [--width INT] [--height INT]
allowed-tools: Bash(python *), Bash(npx *)
---

# /render

Render a SmartArt graphic to PNG using the appropriate engine (custom_svg, mermaid, vega_lite, or matplotlib).

## Step 1: Locate plugin root

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_CUSTOM_SMARTART_ROOT'):
    print(os.environ['JACK_TAR_CUSTOM_SMARTART_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-custom-smartart/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-custom-smartart'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then echo "ERROR: jack-tar-custom-smartart not found" && exit 1; fi
echo "PLUGIN_ROOT=$PLUGIN_ROOT"
```

## Step 2: Resolve spec

If `--spec-file PATH` was given, read the spec JSON from that file.

If inline arguments were given (`--graphic-type`, `--items`, etc.), build a minimal spec:

```python
import json, sys, os

# Inline spec construction example
graphic_type = "$GRAPHIC_TYPE"   # e.g. "flowchart"
items_raw = "$ITEMS"             # semicolon-separated, e.g. "Plan;Build;Ship"
output_path = "$OUTPUT_PATH"     # default: /tmp/<graphic_type>.png
width = int("$WIDTH") if "$WIDTH" else 1920
height = int("$HEIGHT") if "$HEIGHT" else 1080

items = [i.strip() for i in items_raw.split(";") if i.strip()]

spec = {
    "slide_number": 1,
    "graphic_type": graphic_type,
    "engine": "custom_svg",        # default; override in spec file for mermaid/vega_lite/matplotlib
    "enrichment_tier": "pure_programmatic",
    "data": {"items": items},
    "comparator_engines": [],
    "dimensions": {"width": width, "height": height},
    "alt_text": f"{graphic_type} diagram",
}

output_dir = os.path.dirname(output_path) or "/tmp"
print(json.dumps({"spec": spec, "output_dir": output_dir}))
```

If `--spec-file` was given, load the spec directly and extract `output_dir` from the spec's `output_dir` key, or default to `/tmp`.

## Step 3: Render

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json, sys, os

spec_json = '''$SPEC_JSON'''
spec = json.loads(spec_json)

output_dir = '$OUTPUT_DIR'
os.makedirs(output_dir, exist_ok=True)

# Minimal style_guide — renderer uses defaults when palette is absent
style_guide = {}
phase = 'draft'

from src.smartart_renderer import render
entry = render(spec, style_guide, phase, output_dir)

print(json.dumps(entry, indent=2))
"
```

## Step 4: Report

Parse the returned manifest entry and report:

```
RENDER COMPLETE
  graphic_type:   flowchart
  engine_used:    custom_svg
  status:         rendered
  output:         /tmp/smartart_flowchart_slide1.png
  dimensions:     1920 x 1080
  alt_text:       flowchart diagram
  content_hash:   abc123...
```

If `status` is `failed`, report the failure clearly and suggest checking:
- The `engine` field matches an available engine (`custom_svg`, `mermaid`, `vega_lite`, `matplotlib`)
- The `data` field matches the engine's expected shape
- Node.js CLI tools are present (`/verify` to check)

## Notes

- `spec['engine']` must be one of: `custom_svg`, `mermaid`, `vega_lite`, `matplotlib`
- `custom_svg` supports graphic types: `flowchart`, `decision_tree`, `timeline`, `venn`, `swot`, `feature_matrix`, `pipeline_funnel`, `radar_chart`, `gantt`
- `mermaid` and `vega_lite` require Node.js CLIs — run `/verify` first if unsure
- `data` shape varies by engine:
  - `custom_svg`: `{"items": ["Step 1", "Step 2", ...]}` (flat list) or engine-specific keys
  - `mermaid`: `{"diagram": "graph LR\n  A --> B"}` (raw Mermaid DSL)
  - `vega_lite`: `{"spec": {...}}` (Vega-Lite spec object)
  - `matplotlib`: `{"labels": [...], "values": [...]}` (chart data — prefer `/chart` skill for these)
- `comparator_engines` can be a list of additional engines to compare against; the manifest entry will include `comparator_results`
- `enrichment_tier` controls AI enrichment: `pure_programmatic`, `ai_background`, `ai_element_icons`, `full_ai_render`
