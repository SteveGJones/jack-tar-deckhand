# jack-tar-custom-smartart

Data visualisation and custom graphics using SVG, Mermaid, Vega-Lite, and matplotlib. Produces rasterised PNGs for embedding into slides.

9 custom SVG layouts: flowchart, decision tree, timeline, Venn, SWOT, feature matrix, pipeline/funnel, radar chart, Gantt.

## Prerequisites

- Python 3.10+ with matplotlib, seaborn, Pillow
- Node.js with @mermaid-js/mermaid-cli, vega-cli, vega-lite
- Optional: cairosvg (for high-quality SVG rasterisation)

## Skills

| Skill | Purpose |
|-------|---------|
| `/render` | Render a graphic to PNG using the appropriate engine |
| `/chart` | Render a data chart (bar, line, pie, scatter, radar, etc.) |
| `/verify` | Check which rendering engines are available |

## Quick Start

```
/jack-tar-custom-smartart:verify
```
