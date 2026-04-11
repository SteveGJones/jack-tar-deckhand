---
name: chart
description: Render a data chart (bar, line, area, pie, donut, scatter) to PNG using matplotlib. Accepts chart type and data, produces a rasterised PNG.
argument-hint: --type bar|line|area|pie|donut|scatter --data-file PATH [--output PATH] [--style-file PATH]
allowed-tools: Bash(python *)
---

# /chart

Render a data chart to PNG using matplotlib at 300 DPI. Supports chart types: `bar`, `line`, `area`, `pie`, `donut`, `scatter`.

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

## Step 2: Parse arguments

Collect from user input:
- `--type TYPE` — chart type (required): `bar`, `line`, `area`, `pie`, `donut`, `scatter`
- `--data-file PATH` — JSON file containing chart data (required)
- `--output PATH` — output PNG path (default: `/tmp/chart_<type>.png`)
- `--style-file PATH` — optional JSON file containing a StyleGuide dict

Read the data file:

```bash
python3 -c "
import json, sys
with open('$DATA_FILE') as f:
    data = json.load(f)
print(json.dumps(data))
"
```

Data file format depends on chart type:
- **bar / line / area / scatter** — single series: `{"labels": ["Q1","Q2","Q3"], "values": [10,20,30]}`
- **bar / line / area** — multi-series: `{"labels": ["Q1","Q2","Q3"], "series": {"Revenue": [10,20,30], "Cost": [5,8,12]}}`
- **pie / donut**: `{"labels": ["A","B","C"], "values": [40, 35, 25]}`
- **scatter**: `{"labels": ["P1","P2","P3"], "values": [[1,2],[3,4],[5,6]]}` (x,y pairs) or `{"x": [1,3,5], "y": [2,4,6]}`

If `--style-file` is given, read it as a StyleGuide dict. Otherwise pass `None` (default brand colours apply).

## Step 3: Render chart

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json, os

chart_type = '$CHART_TYPE'
output_path = '$OUTPUT_PATH'
data_json = '''$DATA_JSON'''
style_guide_json = '''$STYLE_GUIDE_JSON'''  # empty string = no style guide

data = json.loads(data_json)
style_guide = json.loads(style_guide_json) if style_guide_json.strip() else None

os.makedirs(os.path.dirname(output_path) or '/tmp', exist_ok=True)

from src.render_chart import render_chart
entry = render_chart(
    chart_type=chart_type,
    data=data,
    output_path=output_path,
    style_guide=style_guide,
    width=1920,
    height=1080,
    dpi=300,
)

print(json.dumps(entry, indent=2))
"
```

## Step 4: Report

Parse the returned manifest entry and report:

```
CHART COMPLETE
  chart_id:     chart_bar_slide1_abc123
  chart_type:   bar
  status:       rendered
  output:       /tmp/chart_bar.png
  dimensions:   1920 x 1080
  alt_text:     Bar chart showing Q1 (10), Q2 (20), Q3 (30)
  content_hash: abc123...
```

If the call raises `ValueError` for an unsupported chart type, report the valid types and ask the user to correct their input. Supported chart types: `bar`, `line`, `area`, `pie`, `donut`, `scatter`.

## Notes

- Output is always a PNG at 300 DPI suitable for slide embedding
- Default dimensions are 1920×1080 (16:9). Override with `width` and `height` kwargs if needed
- Brand colours are applied automatically from the StyleGuide when provided; default palette is used otherwise
- For graph-based SmartArt diagrams (flowcharts, Venn, timelines, etc.) use `/render` instead
- `radar` chart type is NOT supported by `render_chart` — use `/render` with `engine=custom_svg` and `graphic_type=radar_chart` for radar/spider charts
