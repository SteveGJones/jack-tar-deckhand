---
name: verify
description: Check Mermaid CLI, Vega CLI, matplotlib, cairosvg availability and report readiness.
allowed-tools: Bash(python *), Bash(npx *), Bash(which *)
---

# /verify

Check whether this plugin's prerequisites are met and report readiness.

## Step 1: Check Python dependencies

```bash
python3 -c "
import json
deps = {}
try:
    import matplotlib; deps['matplotlib'] = matplotlib.__version__
except Exception: deps['matplotlib'] = None
try:
    import seaborn; deps['seaborn'] = seaborn.__version__
except Exception: deps['seaborn'] = None
try:
    from PIL import Image; import PIL; deps['Pillow'] = PIL.__version__
except Exception: deps['Pillow'] = None
try:
    import cairosvg; deps['cairosvg'] = 'installed'
except Exception: deps['cairosvg'] = None
print(json.dumps(deps))
"
```

## Step 2: Check Node.js CLI tools

```bash
npx mmdc --version 2>/dev/null || echo "NOT_FOUND"
npx vl2svg --version 2>/dev/null || echo "NOT_FOUND"
```

## Step 3: Report status

```
PLUGIN: jack-tar-custom-smartart
VERSION: 1.0.0

DEPENDENCIES:
  matplotlib:      READY (3.9.1)
  seaborn:         READY (0.13.2)
  Pillow:          READY (10.2.0)
  cairosvg:        READY (rasteriser: cairosvg)
  Mermaid CLI:     READY (11.12.0)
  Vega CLI:        READY (6.2.0)
  Vega-Lite:       READY (6.4.2)

ENGINES:
  custom_svg:      READY (9 layouts: flowchart, decision_tree, timeline, venn, swot, feature_matrix, pipeline_funnel, radar_chart, gantt)
  mermaid:         READY
  vega_lite:       READY
  matplotlib:      READY (chart types: bar, line, area, pie, donut, scatter, radar)

STATUS: FULLY_AVAILABLE
REASON: All rendering engines available
```

Status rules:
- `STATUS: FULLY_AVAILABLE` — all engines present (matplotlib, Mermaid CLI, Vega CLI)
- `STATUS: PARTIALLY_AVAILABLE` — Mermaid or Vega CLIs missing (custom SVG and matplotlib still work)
- `STATUS: NOT_AVAILABLE` — matplotlib missing (core engine unavailable)
