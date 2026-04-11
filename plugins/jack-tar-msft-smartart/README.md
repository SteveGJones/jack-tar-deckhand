# jack-tar-msft-smartart

Editable PowerPoint SmartArt graphics using native OOXML — speakers can modify them directly in PowerPoint after delivery.

## What it does

Produces genuine PowerPoint SmartArt graphics (not rasterised PNGs) that are fully editable
after the deck is delivered. Speakers can rename nodes, add or remove items, switch to a
different layout, and insert images — all within PowerPoint, Word, or the web apps. 29 layouts
across 9 categories, all sourced from the MIT-licensed `dotnet/Open-XML-SDK` test fixtures.

## Prerequisites

- Python 3.10+
- `python-pptx` and `lxml` (installed via `requirements.txt`)

```
pip install -r plugins/jack-tar-msft-smartart/requirements.txt
```

## Installation

Install via Claude Code marketplace:
```
claude plugin install SteveGJones/jack-tar
```

Or install just this plugin:
```
claude plugin install SteveGJones/jack-tar --plugin jack-tar-msft-smartart
```

## Verify

```
/jack-tar-msft-smartart:verify
```

## Skills

| Skill | Description |
|-------|-------------|
| `/jack-tar-msft-smartart:render` | Generate an editable SmartArt carrier .pptx from a graphic spec |
| `/jack-tar-msft-smartart:inject` | Graft SmartArt from carrier files into an assembled deck .pptx |
| `/jack-tar-msft-smartart:catalog` | List all 29 available layouts with capacity guidance |
| `/jack-tar-msft-smartart:verify` | Check Python dependencies and layout fixture availability |

## Quick Examples

Browse available layouts:
```
/jack-tar-msft-smartart:catalog
```

Render a process diagram (5 steps, editable):
```
/jack-tar-msft-smartart:render {
  "layout_id": "process1",
  "graphic_type": "flowchart",
  "slide_number": 3,
  "data": {"items": ["Research", "Prototype", "Validate", "Harden", "Ship"]}
}
```

Render an org chart with an assistant node:
```
/jack-tar-msft-smartart:render {
  "layout_id": "orgChart1",
  "graphic_type": "org_chart",
  "slide_number": 5,
  "data": {"tree": {"title": "CEO", "children": [
    {"title": "EA", "node_type": "asst"},
    {"title": "CTO", "children": [{"title": "Eng Lead"}]},
    {"title": "CMO"}
  ]}}
}
```

## Layout Categories

| Category | Layout IDs |
|----------|-----------|
| Process | process1, process4, chevron1, hProcess4, hProcess7, hProcess9, hProcess11, lProcess2 |
| Cycle | cycle2, cycle8 |
| Hierarchy | orgChart1, hierarchy2, hierarchy4, hierarchy5, hierarchy6 |
| List | list1, hList6, vList2, vList3, vList4, vList5 |
| Matrix | matrix2 |
| Pyramid | pyramid2 |
| Relationship | venn1, venn3, funnel1, target3 |

Run `/jack-tar-msft-smartart:catalog` for full capacity guidance per layout.

## How It Works

The engine uses template injection: three XML parts per layout (layout, quickStyle, colors)
are extracted from MIT-licensed SDK fixtures. A fresh `data1.xml` is generated for each
graphic. The JS assembler places a named placeholder, then a Python post-process grafts
the diagram parts in — producing a standard `.pptx` that PowerPoint opens natively.

## License

MIT
