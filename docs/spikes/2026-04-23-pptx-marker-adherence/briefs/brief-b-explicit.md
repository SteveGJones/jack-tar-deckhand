# Brief B — Explicit marker protocol

Build a 10-slide conference talk titled "AI Agents That Actually Work" for a developer audience, 20 minutes long. Cover: why most AI agent demos fail in production, the three architectural pillars (planning, memory, tool use), a concrete case study, and a call to action.

## Placeholder protocol (MUST follow exactly)

Some slides need visual enrichment that will be added by a downstream tool. When you build those slides, do not try to generate the visual yourself — instead, leave a **placeholder shape** that the downstream tool will find by name.

The placeholder is a rectangle with:
- Fill: light grey `F0F0F0`
- Border: 1pt dashed `CCCCCC`
- Visible text inside the rectangle equal to the shape's name

Use the PptxGenJS `name` property on the shape so the downstream tool can find it. Naming rules:

| Marker prefix | When to use | Example shape name |
|---------------|-------------|--------------------|
| `IMAGE:`      | Slide needs an AI-generated illustration (e.g. hero image, architecture sketch, conceptual art) | `IMAGE:agent-architecture`, `IMAGE:pillar-planning` |
| `SMARTART:`   | Slide content is a process, cycle, hierarchy, list, or relationship that should become an editable SmartArt diagram | `SMARTART:flowchart`, `SMARTART:cycle`, `SMARTART:pyramid` |
| `BG:`         | Slide would benefit from an atmospheric AI background behind its text. Place a small label shape (~1.5 in × 0.3 in) in the bottom-left corner named `BG:<mood>` | `BG:dramatic-contrast`, `BG:calm-minimal` |

Identifier after the colon: lowercase letters, digits, hyphens, underscores only. Be descriptive — it hints at the visual intent.

## Requested markers (for scoring)

- `IMAGE:*` — at least 2 (e.g. one hero illustration, one architecture sketch)
- `SMARTART:*` — at least 1 (e.g. the three pillars, or the case-study timeline)
- `BG:*` — at least 1 (e.g. the opening or closing slide)
