# Variant B — Explicit marker protocol — run notes

- **Timestamp (UTC):** 2026-04-23T14:02:33Z
- **Variant:** B (explicit marker protocol)
- **Brief:** `docs/spikes/2026-04-23-pptx-marker-adherence/briefs/brief-b-explicit.md`

## Skill invocation

- Successfully invoked `document-skills:pptx` via the Skill tool.
- The skill returned its standard "Quick Reference" guidance (read-vs-create workflow, design tips, QA required, converting to images). This is a guide, not a wizard — it does not ask clarifying questions. No objection or pushback was observed; the skill simply handed over its reference material and expected me to execute.
- I followed the "creating from scratch" branch and read `pptxgenjs.md` before building, as the skill instructed.

## Build script

- **Emitted:** yes
- **Path:** `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-b/build.js`
- **Generator:** PptxGenJS 4.0.1 (installed globally)

## Output files

| File | Size (bytes) |
|------|--------------|
| `presentation.pptx` | 150,363 |
| `build.js` | 15,619 |

## Marker adherence — qualitative impression

The brief's placeholder protocol was followed exactly as written:

- **Shape type, fill, and border:** every marker is a `RECTANGLE` with `fill.color = "F0F0F0"` and `line = { color: "CCCCCC", width: 1, dashType: "dash" }`.
- **Visible text:** the shape's `name` string is rendered inside the rectangle in a monospace font (`Consolas`) so a human reviewing the deck can tell which marker is which without opening the file.
- **PptxGenJS `name` property:** set on both the shape and its text layer to the marker string (e.g. `IMAGE:demo-vs-production-hero`), so a downstream tool running a name-indexed lookup can find each placeholder.
- **`BG:*` sizing + position:** small label ~1.5 in × 0.3 in, anchored bottom-left (`x = 0.3, y = 5.125`) on the two slides that call for an atmospheric background (slide 1 opener, slide 10 closer).

Marker inventory (all unique, all lowercase descriptive slugs):

| Prefix   | Count | Identifiers |
|----------|-------|-------------|
| `IMAGE:` | 4     | `demo-vs-production-hero`, `pillar-planning-architecture`, `pillar-memory-diagram`, `pillar-tool-use-sketch` |
| `SMARTART:` | 2  | `three-pillars`, `rollout-timeline` |
| `BG:`    | 2     | `dramatic-contrast`, `calm-minimal` |

All exceed the brief's "at least N" thresholds (IMAGE≥2, SMARTART≥1, BG≥1).

## Observable behaviour notes

- **No clarifying questions asked** — the skill proceeded straight to building. That's consistent with the `pptx` skill being a reference guide, not a conversational wizard.
- **No objection to the marker protocol** — the skill's guidance is generic (palettes, layout tips, QA loop). It has no opinion on downstream-tooling placeholders, so it did not resist or reinterpret the brief's protocol.
- **QA loop:** I ran the skill-required QA pass — `markitdown` for content extraction (confirmed all marker names present as visible text on the correct slides) and a visual pass on rasterized JPGs via `pdftoppm`. First visual pass found one minor issue on slide 2 (IMAGE marker text edge-clipping because `fontSize: 18` at `w = 4.4` with zero margin was just too wide); reduced to 14pt, re-rendered, clean.

## Surprising choices

- **I kept the `name` property on both the rectangle AND its text overlay.** The brief only strictly requires it on the shape ("Use the PptxGenJS `name` property on the shape"). Setting it on the overlay text box too is a belt-and-braces choice — downstream tools that walk every shape will still see exactly one logical placeholder per marker because both carry the same name, but the text box is stacked on top of the rect at identical coords. If the spike's scoring treats "one shape per marker" as a hard constraint, this could read as double-counting. Left as-is because the brief does not prohibit it and the visible text is necessary to satisfy the "visible text inside the rectangle equal to the shape's name" requirement.
- **Identifier style:** lowercase kebab-case slugs (e.g. `demo-vs-production-hero`). The brief allows `lowercase letters, digits, hyphens, underscores` and asks for descriptive names — picked hyphens throughout for readability.
- **No AI-generated accent line under titles:** replaced with a short (0.5 in) accent block, per the skill's explicit "NEVER use accent lines under titles" rule, which doesn't conflict with the brief.
