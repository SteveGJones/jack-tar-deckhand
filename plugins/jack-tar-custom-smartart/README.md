# jack-tar-custom-smartart

Data visualisation and custom graphics using SVG, Mermaid, Vega-Lite, and matplotlib.

## What it does

Renders data visualisations and custom infographics as rasterised PNGs for embedding into
presentation slides. Uses multiple rendering engines depending on the graphic type: Mermaid
for graph-based diagrams, Vega-Lite for data charts, and custom SVG Python layouts for
spatial infographics (SWOT, Venn, feature matrices, etc.). Each graphic type routes
automatically to the engine that produces the best aspect ratio.

## Prerequisites

- Python 3.10+ with `matplotlib`, `seaborn`, `Pillow`
- Node.js with:
  - `@mermaid-js/mermaid-cli` (`npm install -g @mermaid-js/mermaid-cli`)
  - `vega-cli` and `vega-lite` (`npm install -g vega vega-lite vega-cli`)
- Optional: `cairosvg` for higher-quality SVG rasterisation

```
pip install -r plugins/jack-tar-custom-smartart/requirements.txt
```

## Installation

Install via Claude Code marketplace:
```
claude plugin install SteveGJones/jack-tar
```

Or install just this plugin:
```
claude plugin install SteveGJones/jack-tar --plugin jack-tar-custom-smartart
```

## Verify

```
/jack-tar-custom-smartart:verify
```

This reports which rendering engines are available (Mermaid, Vega, SVG, matplotlib).

## Skills

| Skill | Description |
|-------|-------------|
| `/jack-tar-custom-smartart:render` | Render a graphic to PNG using the best available engine for the type |
| `/jack-tar-custom-smartart:chart` | Render a data chart (bar, line, pie, scatter, radar, etc.) |
| `/jack-tar-custom-smartart:verify` | Check which rendering engines are installed and available |

## Supported Graphic Types

| Type | Engine | Notes |
|------|--------|-------|
| flowchart | Mermaid (simple) / SVG grid (4+ nodes) | Auto-routes for aspect ratio |
| decision_tree | Mermaid (simple) / SVG 2-col (3+ rules) | Auto-routes for complexity |
| timeline | Custom SVG | Horizontal swimlane layout |
| venn | Custom SVG | 2–4 circles with overlap labels |
| swot | Custom SVG | 2×2 quadrant with coloured sections |
| feature_matrix | Custom SVG | Row/column comparison grid |
| pipeline_funnel | Custom SVG | Narrowing funnel with stage labels |
| radar | Vega-Lite | Multi-axis spider chart |
| gantt | Mermaid | Horizontal bar timeline |
| bar_chart | Vega-Lite | Grouped or stacked bars |
| line_chart | Vega-Lite | Single or multi-series line |

## Quick Examples

Render a flowchart:
```
/jack-tar-custom-smartart:render {
  "graphic_type": "flowchart",
  "nodes": ["Ingest", "Validate", "Transform", "Load", "Report"]
}
```

Render a data bar chart:
```
/jack-tar-custom-smartart:chart {
  "chart_type": "bar",
  "title": "Quarterly Revenue",
  "data": {"Q1": 120, "Q2": 145, "Q3": 198, "Q4": 221}
}
```

## Notes

- Output is a rasterised PNG — graphics are not editable in PowerPoint after delivery.
  Use `jack-tar-msft-smartart` if you need editable SmartArt.
- The draft-phase comparator in the deckhand pipeline renders competing engines for the same
  graphic and uses the image reviewer to pick the winner before production.

## License

MIT
