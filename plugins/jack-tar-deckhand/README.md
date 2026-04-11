# jack-tar-deckhand

Full presentation engineering pipeline — create conference-quality PowerPoint decks through an orchestrated multi-step process.

## What it does

Orchestrates the complete deck-creation pipeline: brand profiling, style derivation,
narrative architecture, rendering strategy classification, SmartArt selection and extraction,
speaker note generation, image generation (via engine plugins), assembly, and quality
assurance. The conductor agent drives a 11-step pipeline from a plain-English talk brief to
a production-ready `.pptx`. Engine plugins (`jack-tar-ollama`, `jack-tar-cloud`,
`jack-tar-msft-smartart`, `jack-tar-custom-smartart`) plug in for image and SmartArt
generation — the deckhand pipeline works without them but produces text-only slides.

## Prerequisites

- Python 3.10+ with `jsonschema`, `Pillow`, `python-pptx`
- Node.js with `pptxgenjs`

```
pip install -r plugins/jack-tar-deckhand/requirements.txt
npm install
```

## Optional Engine Plugins

| Plugin | What it adds |
|--------|-------------|
| `jack-tar-ollama` | Local AI image generation (draft tier, free) |
| `jack-tar-cloud` | Cloud AI image generation (production tier) |
| `jack-tar-msft-smartart` | Editable PowerPoint SmartArt (29 layouts) |
| `jack-tar-custom-smartart` | Data visualisation via SVG / Mermaid / Vega |

## Installation

Install the full suite (recommended):
```
claude plugin install SteveGJones/jack-tar
```

Or install just this plugin:
```
claude plugin install SteveGJones/jack-tar --plugin jack-tar-deckhand
```

## Verify

```
/jack-tar-deckhand:verify
```

Reports pipeline readiness and which engine plugins are detected.

## Skills

| Skill | Description |
|-------|-------------|
| `/jack-tar-deckhand:brand-manager` | Extract or load a reusable brand profile from assets or a URL |
| `/jack-tar-deckhand:slide-stylist` | Derive palette, typography, and layout rules from the brand profile |
| `/jack-tar-deckhand:narrative-architect` | Build narrative arc and slide outline from a talk brief |
| `/jack-tar-deckhand:strategy-map` | Classify each slide's rendering strategy (full_render, background, composed, etc.) |
| `/jack-tar-deckhand:smartart-selector` | Select SmartArt graphic types for applicable slides |
| `/jack-tar-deckhand:smartart-extractor` | Transform approved slide content into SmartArt engine specs |
| `/jack-tar-deckhand:speaker-notes-writer` | Generate timed, cue-marked speaker notes for every slide |
| `/jack-tar-deckhand:imagegen-bridge` | Route image generation requests to available engine plugins |
| `/jack-tar-deckhand:deck-assembler` | Assemble the final `.pptx` from all contracts using PptxGenJS |
| `/jack-tar-deckhand:deck-qa` | Run 30 automated anti-pattern checks against the assembled deck |
| `/jack-tar-deckhand:verify` | Check pipeline readiness and detect available engine plugins |

## Pipeline Overview

The deck conductor agent drives an 11-step pipeline. Each step reads and writes JSON
contracts in a `DeckContext` directory (`tmp/deck/` by default):

```
1. brand-manager      → brand-profile.json
2. slide-stylist      → style-guide.json
3. narrative-architect → outline.json
4. smartart-selector  → smartart-recommendations.json
5. strategy-map       → strategy-map.json
6. smartart-extractor → smartart-spec.json + carriers (via msft-smartart)
7. speaker-notes-writer → speaker-notes.json
8. imagegen-bridge    → image-manifest.json (via ollama or cloud plugins)
9. deck-assembler     → output/presentation.pptx (Node.js + PptxGenJS)
10. pptx_native inject → grafts editable SmartArt into the deck
11. deck-qa           → qa-report.json + pass/fail summary
```

**Rendering strategies** per slide:
- `full_render` — entire slide as AI-generated image (title, section dividers)
- `background` — atmospheric AI background + text in template zones
- `backdrop` — structured AI scene + vision analysis for text positioning
- `pragmatic_composition` — individual AI elements assembled at exact positions
- `composed` — standard PptxGenJS layout (diagrams, charts, code slides)
- `smartart` — pptx_native editable SmartArt or custom SVG graphic

**Render funnel** (when image plugins are available):
1. Ollama draft (free) — iterate up to 10× at zero cost
2. Cloud low 720p (cheap) — if reviewer requests upgrade
3. Cloud full 2K+ (production) — for approved production slides only

## Quick Start

```
/jack-tar-deckhand:verify
```

Then ask the deck conductor agent to build a deck:

```
Using the deck conductor, build a 12-slide conference talk on "The Future of Developer
Tooling" for a technical audience at a 30-minute keynote slot.
```

The conductor walks through each pipeline step, showing you options at key decision points
(narrative arc, SmartArt types, rendering strategies) before committing.

## License

MIT
