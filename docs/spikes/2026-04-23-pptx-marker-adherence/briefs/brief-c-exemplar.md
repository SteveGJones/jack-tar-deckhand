# Brief C — Protocol + worked example

Build a 10-slide conference talk titled "AI Agents That Actually Work" for a developer audience, 20 minutes long. Cover: why most AI agent demos fail in production, the three architectural pillars (planning, memory, tool use), a concrete case study, and a call to action.

## Placeholder protocol (MUST follow exactly)

Some slides need visual enrichment that will be added by a downstream tool. When you build those slides, do not try to generate the visual yourself — instead, leave a **placeholder shape** that the downstream tool will find by name.

| Marker prefix | When to use | Example shape name |
|---------------|-------------|--------------------|
| `IMAGE:`      | AI illustration | `IMAGE:agent-architecture` |
| `SMARTART:`   | Process / cycle / hierarchy / relationship | `SMARTART:flowchart` |
| `BG:`         | Atmospheric AI background (place a small corner label shape) | `BG:dramatic-contrast` |

### Worked example — what a slide with an IMAGE marker should look like in your build script

```javascript
// Slide 3: "Why most agents fail"
const slide3 = pres.addSlide();
slide3.addText("Why most agents fail", { x: 0.5, y: 0.3, w: 9, h: 0.8, fontSize: 32, bold: true });
slide3.addText([
  { text: "Prompt engineering hits a ceiling", options: { bullet: true } },
  { text: "No persistent memory", options: { bullet: true } },
  { text: "Tool use is brittle", options: { bullet: true } },
], { x: 0.5, y: 1.5, w: 4.5, h: 3, fontSize: 20 });

// IMAGE placeholder on the right 40% of the slide
slide3.addShape(pres.ShapeType.rect, {
  x: 5.5, y: 1.5, w: 4, h: 3,
  fill: { color: "F0F0F0" },
  line: { color: "CCCCCC", width: 1, dashType: "dash" },
  name: "IMAGE:agents-failing",        // <-- shape name matters
});
slide3.addText("IMAGE:agents-failing", { x: 5.5, y: 2.8, w: 4, h: 0.5, align: "center", color: "888888", fontSize: 14 });
```

### Worked example — BG corner label

```javascript
// Slide 1: title — wants a dramatic background
const slide1 = pres.addSlide();
slide1.addText("AI Agents That Actually Work", { x: 0.5, y: 2.5, w: 9, h: 1.5, fontSize: 48, bold: true });

// Small corner label — the BG marker
slide1.addShape(pres.ShapeType.rect, {
  x: 0.2, y: 6.8, w: 1.8, h: 0.3,
  fill: { color: "F0F0F0" },
  line: { color: "CCCCCC", width: 1, dashType: "dash" },
  name: "BG:dramatic-opening",
});
slide1.addText("BG:dramatic-opening", { x: 0.2, y: 6.8, w: 1.8, h: 0.3, align: "center", color: "888888", fontSize: 10 });
```

Follow this pattern for every slide that needs a marker.

## Requested markers (for scoring)

- `IMAGE:*` — at least 2
- `SMARTART:*` — at least 1
- `BG:*` — at least 1
